from datetime import date, timedelta
from random import choice, randint

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import RoleName
from app.core.security import hash_password
from app.db import base  # noqa: F401
from app.db.session import SessionLocal
from app.models.employee import Employee
from app.models.role import Role
from app.models.user import User

DEPARTMENTS = ["Engineering", "HR", "Finance", "Operations", "Sales"]
DESIGNATIONS = ["Associate", "Executive", "Analyst", "Manager", "Specialist"]


def get_or_create_role(db: Session, role_name: str) -> Role:
    role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
    if role is None:
        role = Role(name=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)
    return role


def create_user_if_missing(db: Session, email: str, password: str, role_id: int) -> User:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user:
        return user

    user = User(email=email, password_hash=hash_password(password), role_id=role_id, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_employee_profile_if_missing(db: Session, user_id: int, employee_code: str, name: str) -> None:
    existing = db.execute(select(Employee).where(Employee.user_id == user_id)).scalar_one_or_none()
    if existing:
        return

    emp_code_exists = db.execute(select(Employee).where(Employee.employee_id == employee_code)).scalar_one_or_none()
    if emp_code_exists:
        return

    joining = date.today() - timedelta(days=randint(30, 1500))
    employee = Employee(
        user_id=user_id,
        employee_id=employee_code,
        name=name,
        department=choice(DEPARTMENTS),
        designation=choice(DESIGNATIONS),
        joining_date=joining,
        base_salary=float(randint(25000, 120000)),
        salary_type="monthly",
        is_active=True,
    )
    db.add(employee)
    db.commit()


def run() -> None:
    db: Session = SessionLocal()
    try:
        admin_role = get_or_create_role(db, RoleName.ADMIN.value)
        hr_role = get_or_create_role(db, RoleName.HR.value)
        emp_role = get_or_create_role(db, RoleName.EMPLOYEE.value)

        # 2 admins
        for i in range(1, 3):
            email = f"admin{i}@hrms.com"
            create_user_if_missing(db, email, "Admin@12345", admin_role.id)

        # 4 HRs
        for i in range(1, 5):
            email = f"hr{i}@hrms.com"
            user = create_user_if_missing(db, email, "Hr@12345", hr_role.id)
            create_employee_profile_if_missing(db, user.id, f"HR{i:03}", f"HR User {i}")

        # 50 employees
        for i in range(1, 51):
            email = f"emp{i:03}@hrms.com"
            user = create_user_if_missing(db, email, "Emp@12345", emp_role.id)
            create_employee_profile_if_missing(db, user.id, f"EMP{i:03}", f"Employee {i}")

        print("Population complete: 2 admins, 4 HRs, 50 employees (duplicates skipped).")
        print("Default passwords: Admin@12345 / Hr@12345 / Emp@12345")
    finally:
        db.close()


if __name__ == "__main__":
    run()
