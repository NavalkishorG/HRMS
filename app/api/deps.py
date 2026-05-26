from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import RoleName
from app.core.exceptions import DomainError, ForbiddenError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.employee import Employee
from app.models.user import User


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise DomainError('missing_token', 'Authorization token is required', 401)

    payload = decode_token(credentials.credentials)
    if payload.get('type') != 'access':
        raise DomainError('invalid_token_type', 'Access token required', 401)

    user = db.execute(select(User).where(User.id == int(payload['sub']))).scalar_one_or_none()
    if user is None:
        raise DomainError('invalid_user', 'User not found', 401)

    employee = db.execute(select(Employee).where(Employee.user_id == user.id)).scalar_one_or_none()
    return {'id': user.id, 'role': payload.get('role'), 'employee_code': employee.employee_id if employee else None}


def require_roles(*allowed_roles: RoleName):
    allowed = {r.value for r in allowed_roles}

    def checker(current=Depends(get_current_user)):
        if current['role'] not in allowed:
            raise ForbiddenError('You do not have permission to access this resource')
        return current

    return checker
