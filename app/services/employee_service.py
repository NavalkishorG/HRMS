from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError, NotFoundError
from app.models.employee import Employee
from app.models.role import Role
from app.models.user import User
from app.schemas.common import EmployeeCreateRequest, EmployeeUpdateRequest
from app.core.security import hash_password
from app.services.auth_service import enforce_delete_rule


def create_employee(db: Session, payload: EmployeeCreateRequest) -> Employee:
    if payload.joining_date > date.today():
        raise DomainError('invalid_joining_date', 'Joining date cannot be in the future')

    duplicate_emp = db.execute(select(Employee).where(Employee.employee_id == payload.employee_id)).scalar_one_or_none()
    if duplicate_emp:
        raise DomainError('duplicate_employee_id', 'Employee ID already exists', 409)

    duplicate_email = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if duplicate_email:
        raise DomainError('duplicate_email', 'Email already exists', 409)

    role = db.execute(select(Role).where(Role.name == payload.role)).scalar_one_or_none()
    if role is None:
        raise NotFoundError(f'Role {payload.role} not found')

    user = User(email=payload.email, password_hash=hash_password('ChangeMe@123'), role_id=role.id)
    db.add(user)
    db.flush()

    employee = Employee(
        user_id=user.id,
        employee_id=payload.employee_id,
        name=payload.name,
        department=payload.department,
        designation=payload.designation,
        joining_date=payload.joining_date,
        base_salary=payload.base_salary,
        salary_type=payload.salary_type,
    )
    db.add(employee)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError('duplicate_employee', 'Employee ID or email already exists', 409) from exc
    db.refresh(employee)
    return employee


def update_employee(db: Session, employee_id: str, payload: EmployeeUpdateRequest) -> Employee:
    employee = db.execute(select(Employee).where(Employee.employee_id == employee_id)).scalar_one_or_none()
    if employee is None:
        raise NotFoundError('Employee not found')
    if not employee.is_active:
        raise DomainError('inactive_employee', 'Cannot update inactive employee', 409)

    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(employee, key, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError('employee_update_conflict', 'Could not update employee due to a data conflict', 409) from exc
    db.refresh(employee)
    return employee


def deactivate_employee(db: Session, employee_id: str, actor_role: str) -> dict:
    employee = db.execute(select(Employee).where(Employee.employee_id == employee_id)).scalar_one_or_none()
    if employee is None:
        raise NotFoundError('Employee not found')
    target_user = db.execute(select(User).where(User.id == employee.user_id)).scalar_one_or_none()
    if target_user is None:
        raise NotFoundError('User not found for employee')
    target_role = db.execute(select(Role).where(Role.id == target_user.role_id)).scalar_one()
    enforce_delete_rule(actor_role, target_role.name)
    employee.is_active = False
    target_user.is_active = False
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError('employee_deactivate_conflict', 'Could not deactivate employee due to a data conflict', 409) from exc
    return {'message': 'Employee deactivated'}


def list_employees(db: Session) -> list[Employee]:
    return list(db.execute(select(Employee).order_by(Employee.id.desc())).scalars().all())


def get_employee(db: Session, employee_id: str) -> Employee:
    employee = db.execute(select(Employee).where(Employee.employee_id == employee_id)).scalar_one_or_none()
    if employee is None:
        raise NotFoundError('Employee not found')
    return employee
