from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError, NotFoundError
from app.models.employee import Employee
from app.models.payroll import PayrollRecord
from app.services.attendance_service import monthly_summary
from app.services.salary_service import calculate_final_salary

PAYSLIP_DIR = Path('generated_payslips')


def _pdf_escape(text: str) -> str:
    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def _build_simple_pdf(lines: list[str]) -> bytes:
    content_parts = ["BT /F1 12 Tf 50 780 Td 14 TL"]
    for idx, line in enumerate(lines):
        if idx == 0:
            content_parts.append(f"({_pdf_escape(line)}) Tj")
        else:
            content_parts.append(f"T* ({_pdf_escape(line)}) Tj")
    content_parts.append("ET")
    stream = "\n".join(content_parts).encode("latin-1", errors="replace")

    objs: list[bytes] = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>")
    objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objs.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objs, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objs) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


def generate_payroll(db: Session, employee_code: str, month: str, bonuses: float = 0) -> PayrollRecord:
    employee = db.execute(select(Employee).where(Employee.employee_id == employee_code)).scalar_one_or_none()
    if employee is None:
        raise NotFoundError('Employee not found')

    existing = db.execute(select(PayrollRecord).where(and_(PayrollRecord.employee_id == employee.id, PayrollRecord.month == month))).scalar_one_or_none()
    if existing:
        raise DomainError('duplicate_payroll', 'Salary cannot generate twice for same month', 409)

    summary = monthly_summary(db, employee_code, month)
    salary = calculate_final_salary(employee.base_salary, summary['late_marks'], summary['leave_count'], summary['overtime_hours'], bonuses)

    deductions = salary['late_deductions'] + salary['leave_deductions']
    if salary['final_salary'] < 0:
        raise DomainError('negative_salary', 'Negative salary not allowed', 400)

    row = PayrollRecord(
        employee_id=employee.id,
        month=month,
        working_days=summary['working_days'],
        present_days=summary['present_days'],
        leave_count=summary['leave_count'],
        late_marks=summary['late_marks'],
        overtime_hours=summary['overtime_hours'],
        bonuses=bonuses,
        deductions=round(deductions, 2),
        final_salary=salary['final_salary'],
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError('duplicate_payroll', 'Salary cannot generate twice for same month', 409) from exc
    db.refresh(row)
    return row


def list_payroll_history(db: Session, employee_code: str) -> list[PayrollRecord]:
    employee = db.execute(select(Employee).where(Employee.employee_id == employee_code)).scalar_one_or_none()
    if employee is None:
        raise NotFoundError('Employee not found')
    return list(db.execute(select(PayrollRecord).where(PayrollRecord.employee_id == employee.id).order_by(PayrollRecord.month.desc())).scalars().all())


def generate_payslip_file(db: Session, employee_code: str, month: str) -> PayrollRecord:
    employee = db.execute(select(Employee).where(Employee.employee_id == employee_code)).scalar_one_or_none()
    if employee is None:
        raise NotFoundError('Employee not found')

    payroll = db.execute(select(PayrollRecord).where(and_(PayrollRecord.employee_id == employee.id, PayrollRecord.month == month))).scalar_one_or_none()
    if payroll is None:
        raise NotFoundError('Payroll not found for given month')

    PAYSLIP_DIR.mkdir(parents=True, exist_ok=True)
    file_path = PAYSLIP_DIR / f'{employee.employee_id}_{month}.pdf'
    lines = [
        'Payslip',
        'Company Logo: [Placeholder]',
        f'Employee: {employee.name}',
        f'Department: {employee.department}',
        f'Month: {payroll.month}',
        f'Working Days: {payroll.working_days}',
        f'Present Days: {payroll.present_days}',
        f'Leave Count: {payroll.leave_count}',
        f'Overtime Hours: {payroll.overtime_hours}',
        f'Bonuses: {payroll.bonuses}',
        f'Deductions: {payroll.deductions}',
        f'Final Salary: {payroll.final_salary}',
    ]
    file_path.write_bytes(_build_simple_pdf(lines))
    payroll.payslip_path = str(file_path)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError('payslip_update_conflict', 'Could not save payslip metadata', 409) from exc
    db.refresh(payroll)
    return payroll
