from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import RoleName
from app.core.security import hash_password
from app.db import base 
from app.db.session import SessionLocal
from app.models.role import Role
from app.models.user import User


def run_seed() -> None:
    db: Session = SessionLocal()
    try:
        for role_name in [RoleName.ADMIN.value, RoleName.HR.value, RoleName.EMPLOYEE.value]:
            role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
            if role is None:
                db.add(Role(name=role_name))
        db.commit()

        admin_role = db.execute(select(Role).where(Role.name == RoleName.ADMIN.value)).scalar_one()
        admin = db.execute(select(User).where(User.email == 'admin@hrms.local')).scalar_one_or_none()
        if admin is None:
            db.add(User(email='admin@hrms.local', password_hash=hash_password('Admin@12345'), role_id=admin_role.id))
            db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    run_seed()
    print('Seeding complete.')
