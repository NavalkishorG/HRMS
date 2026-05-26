from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.constants import RoleName
from app.db.session import get_db
from app.schemas.common import AttendanceCorrectionRequest
from app.services.attendance_service import attendance_history, check_in, check_out, correct_attendance, monthly_summary


router = APIRouter()


@router.post('/check-in')
def do_checkin(db: Session = Depends(get_db), current=Depends(require_roles(RoleName.EMPLOYEE, RoleName.ADMIN, RoleName.HR))):
    if not current.get('employee_code'):
        return {'message': 'No employee profile linked to this account'}
    return check_in(db, current['employee_code'])


@router.post('/check-out')
def do_checkout(db: Session = Depends(get_db), current=Depends(require_roles(RoleName.EMPLOYEE, RoleName.ADMIN, RoleName.HR))):
    if not current.get('employee_code'):
        return {'message': 'No employee profile linked to this account'}
    return check_out(db, current['employee_code'])


@router.get('/me/history')
def my_history(db: Session = Depends(get_db), current=Depends(get_current_user)):
    if not current.get('employee_code'):
        return []
    return attendance_history(db, current['employee_code'])


@router.get('/reports/{employee_id}')
def employee_report(employee_id: str, month: str = Query(..., pattern=r'^\d{4}-\d{2}$'), db: Session = Depends(get_db), _=Depends(require_roles(RoleName.ADMIN, RoleName.HR))):
    return monthly_summary(db, employee_id, month)


@router.patch('/corrections/{employee_id}')
def attendance_correction(
    employee_id: str,
    payload: AttendanceCorrectionRequest,
    db: Session = Depends(get_db),
    _=Depends(require_roles(RoleName.ADMIN, RoleName.HR)),
):
    row = correct_attendance(db, employee_id, payload.attendance_date, payload.check_in_time, payload.check_out_time)
    return {
        'employee_id': employee_id,
        'attendance_date': str(row.attendance_date),
        'check_in_time': row.check_in_time,
        'check_out_time': row.check_out_time,
        'worked_hours': row.worked_hours,
        'late_mark': row.late_mark,
        'half_day': row.half_day,
        'overtime_hours': row.overtime_hours,
    }
