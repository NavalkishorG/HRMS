from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.constants import RoleName
from app.core.exceptions import ForbiddenError
from app.db.session import get_db
from app.schemas.common import EmployeeCreateRequest, EmployeeResponse, EmployeeUpdateRequest
from app.services.employee_service import create_employee, deactivate_employee, get_employee, list_employees, update_employee


router = APIRouter()


@router.post('', response_model=EmployeeResponse)
def create(payload: EmployeeCreateRequest, db: Session = Depends(get_db), _=Depends(require_roles(RoleName.ADMIN, RoleName.HR))):
    return create_employee(db, payload)


@router.get('', response_model=list[EmployeeResponse])
def list_all(db: Session = Depends(get_db), _=Depends(require_roles(RoleName.ADMIN, RoleName.HR))):
    return list_employees(db)


@router.get('/{employee_id}', response_model=EmployeeResponse)
def get_one(employee_id: str, db: Session = Depends(get_db), current=Depends(require_roles(RoleName.ADMIN, RoleName.HR, RoleName.EMPLOYEE))):
    if current['role'] == RoleName.EMPLOYEE.value and current.get('employee_code') != employee_id:
        raise ForbiddenError('Employees can only access their own profile')
    return get_employee(db, employee_id)


@router.put('/{employee_id}', response_model=EmployeeResponse)
def update(employee_id: str, payload: EmployeeUpdateRequest, db: Session = Depends(get_db), _=Depends(require_roles(RoleName.ADMIN, RoleName.HR))):
    return update_employee(db, employee_id, payload)


@router.delete('/{employee_id}')
def deactivate(employee_id: str, db: Session = Depends(get_db), current=Depends(require_roles(RoleName.ADMIN, RoleName.HR))):
    return deactivate_employee(db, employee_id, current['role'])
