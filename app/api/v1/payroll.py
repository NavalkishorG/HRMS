from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.constants import RoleName
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.session import get_db
from app.schemas.common import PayrollGenerateRequest
from app.services.payroll_service import PAYSLIP_DIR, generate_payroll, generate_payslip_file, list_payroll_history


router = APIRouter()


@router.post('/generate')
def generate(payload: PayrollGenerateRequest, db: Session = Depends(get_db), _=Depends(require_roles(RoleName.ADMIN, RoleName.HR))):
    row = generate_payroll(db, payload.employee_id, payload.month, payload.bonuses)
    return {
        'employee': row.employee.name,
        'month': row.month,
        'working_days': row.working_days,
        'present_days': row.present_days,
        'late_marks': row.late_marks,
        'overtime_hours': row.overtime_hours,
        'deductions': row.deductions,
        'final_salary': row.final_salary,
    }


@router.get('/history/{employee_id}')
def history(employee_id: str, db: Session = Depends(get_db), current=Depends(require_roles(RoleName.ADMIN, RoleName.HR, RoleName.EMPLOYEE))):
    if current['role'] == RoleName.EMPLOYEE.value and current.get('employee_code') != employee_id:
        raise ForbiddenError('Employees can only access their own payroll history')
    rows = list_payroll_history(db, employee_id)
    return rows


@router.post('/payslips/{employee_id}/{month}')
def create_payslip(employee_id: str, month: str, db: Session = Depends(get_db), _=Depends(require_roles(RoleName.ADMIN, RoleName.HR))):
    row = generate_payslip_file(db, employee_id, month)
    return {'payslip_path': row.payslip_path}


@router.get('/payslips/download')
def download(path: str = Query(...), current=Depends(require_roles(RoleName.ADMIN, RoleName.HR, RoleName.EMPLOYEE))):
    requested = Path(path).resolve()
    base = PAYSLIP_DIR.resolve()
    if base not in requested.parents:
        raise ForbiddenError('Invalid payslip path')
    if not requested.is_file():
        raise NotFoundError('Payslip file not found')
    if current['role'] == RoleName.EMPLOYEE.value:
        emp_code = current.get('employee_code')
        if not emp_code or not requested.name.startswith(f'{emp_code}_'):
            raise ForbiddenError('Employees can only download their own payslips')
    return FileResponse(path=str(requested), filename=requested.name)
