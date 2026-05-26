from calendar import monthrange
from datetime import date, datetime, time, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import DomainError, NotFoundError
from app.models.attendance import AttendanceRecord
from app.models.employee import Employee


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _office_start_today() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.combine(now.date(), time(settings.OFFICE_START_HOUR, settings.OFFICE_START_MINUTE), tzinfo=timezone.utc)


def _late_cutoff_today() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.combine(now.date(), time(settings.LATE_AFTER_HOUR, settings.LATE_AFTER_MINUTE), tzinfo=timezone.utc)


def _late_cutoff_for_date(day: date) -> datetime:
    return datetime.combine(day, time(settings.LATE_AFTER_HOUR, settings.LATE_AFTER_MINUTE), tzinfo=timezone.utc)


def check_in(db: Session, employee_code: str) -> dict:
    employee = db.execute(select(Employee).where(Employee.employee_id == employee_code)).scalar_one_or_none()
    if employee is None:
        raise NotFoundError('Employee not found')

    today = datetime.now(timezone.utc).date()
    existing = db.execute(select(AttendanceRecord).where(and_(AttendanceRecord.employee_id == employee.id, AttendanceRecord.attendance_date == today))).scalar_one_or_none()
    if existing and existing.check_in_time is not None and existing.check_out_time is None:
        raise DomainError('double_check_in', 'Double check-in not allowed', 409)
    if existing and existing.check_out_time is not None:
        raise DomainError('already_closed', 'Attendance already completed for today', 409)

    now = datetime.now(timezone.utc)
    late_mark = now > _late_cutoff_today()

    if existing is None:
        record = AttendanceRecord(
            employee_id=employee.id,
            attendance_date=today,
            check_in_time=now,
            late_mark=late_mark,
        )
        db.add(record)
    else:
        existing.check_in_time = now
        existing.late_mark = late_mark

    db.commit()
    return {'message': 'Check-in successful'}


def check_out(db: Session, employee_code: str) -> dict:
    employee = db.execute(select(Employee).where(Employee.employee_id == employee_code)).scalar_one_or_none()
    if employee is None:
        raise NotFoundError('Employee not found')

    today = datetime.now(timezone.utc).date()
    record = db.execute(select(AttendanceRecord).where(and_(AttendanceRecord.employee_id == employee.id, AttendanceRecord.attendance_date == today))).scalar_one_or_none()
    if record is None or record.check_in_time is None:
        raise DomainError('missing_checkin', 'Check-out before check-in is invalid', 400)
    if record.check_out_time is not None:
        raise DomainError('double_checkout', 'Already checked out for today', 409)

    now = datetime.now(timezone.utc)
    if now < record.check_in_time:
        raise DomainError('invalid_time_order', 'Check-out before check-in invalid', 400)

    worked_hours = (now - record.check_in_time).total_seconds() / 3600
    overtime = max(0.0, worked_hours - settings.FULL_DAY_HOURS)
    if overtime > settings.OVERTIME_MAX_HOURS_PER_DAY:
        raise DomainError('overtime_exceeded', 'Overtime cannot exceed configured limits', 400)

    record.check_out_time = now
    record.worked_hours = round(worked_hours, 2)
    record.half_day = worked_hours < settings.HALF_DAY_MIN_HOURS
    record.overtime_hours = round(overtime, 2)
    db.commit()

    return {'message': 'Check-out successful'}


def attendance_history(db: Session, employee_code: str) -> list[AttendanceRecord]:
    employee = db.execute(select(Employee).where(Employee.employee_id == employee_code)).scalar_one_or_none()
    if employee is None:
        raise NotFoundError('Employee not found')
    return list(db.execute(select(AttendanceRecord).where(AttendanceRecord.employee_id == employee.id).order_by(AttendanceRecord.attendance_date.desc())).scalars().all())


def monthly_summary(db: Session, employee_code: str, month: str) -> dict:
    employee = db.execute(select(Employee).where(Employee.employee_id == employee_code)).scalar_one_or_none()
    if employee is None:
        raise NotFoundError('Employee not found')

    try:
        y, m = month.split('-')
        year = int(y)
        mon = int(m)
    except (ValueError, TypeError):
        raise DomainError('invalid_month', 'Month must be YYYY-MM', 400)
    if mon < 1 or mon > 12:
        raise DomainError('invalid_month', 'Month must be YYYY-MM', 400)

    start = date(year, mon, 1)
    end = date(year, mon, monthrange(year, mon)[1])
    rows = list(
        db.execute(
            select(AttendanceRecord).where(
                and_(AttendanceRecord.employee_id == employee.id, AttendanceRecord.attendance_date >= start, AttendanceRecord.attendance_date <= end)
            )
        ).scalars().all()
    )

    present_days = sum(1 for r in rows if r.check_in_time)
    late_marks = sum(1 for r in rows if r.late_mark)
    overtime_hours = round(sum(r.overtime_hours for r in rows), 2)
    leave_count = max(0, monthrange(year, mon)[1] - present_days)

    return {
        'working_days': monthrange(year, mon)[1],
        'present_days': present_days,
        'leave_count': leave_count,
        'late_marks': late_marks,
        'overtime_hours': overtime_hours,
    }


def correct_attendance(
    db: Session,
    employee_code: str,
    attendance_date: date,
    check_in_time: datetime | None,
    check_out_time: datetime | None,
) -> AttendanceRecord:
    employee = db.execute(select(Employee).where(Employee.employee_id == employee_code)).scalar_one_or_none()
    if employee is None:
        raise NotFoundError('Employee not found')
    if attendance_date > datetime.now(timezone.utc).date():
        raise DomainError('future_attendance', 'Future attendance invalid', 400)
    if check_in_time is None and check_out_time is None:
        raise DomainError('invalid_correction', 'At least one of check-in or check-out must be provided', 400)

    record = db.execute(
        select(AttendanceRecord).where(
            and_(AttendanceRecord.employee_id == employee.id, AttendanceRecord.attendance_date == attendance_date)
        )
    ).scalar_one_or_none()
    if record is None:
        record = AttendanceRecord(employee_id=employee.id, attendance_date=attendance_date)
        db.add(record)

    if check_in_time is not None:
        record.check_in_time = _to_utc(check_in_time)
    if check_out_time is not None:
        record.check_out_time = _to_utc(check_out_time)

    if record.check_in_time is None:
        raise DomainError('missing_checkin', 'Check-in is required for attendance correction', 400)
    if record.check_out_time is not None and record.check_out_time < record.check_in_time:
        raise DomainError('invalid_time_order', 'Check-out before check-in invalid', 400)

    record.late_mark = record.check_in_time > _late_cutoff_for_date(attendance_date)
    if record.check_out_time is None:
        record.worked_hours = 0.0
        record.half_day = False
        record.overtime_hours = 0.0
    else:
        worked_hours = (record.check_out_time - record.check_in_time).total_seconds() / 3600
        overtime = max(0.0, worked_hours - settings.FULL_DAY_HOURS)
        if overtime > settings.OVERTIME_MAX_HOURS_PER_DAY:
            raise DomainError('overtime_exceeded', 'Overtime cannot exceed configured limits', 400)
        record.worked_hours = round(worked_hours, 2)
        record.half_day = worked_hours < settings.HALF_DAY_MIN_HOURS
        record.overtime_hours = round(overtime, 2)

    db.commit()
    db.refresh(record)
    return record
