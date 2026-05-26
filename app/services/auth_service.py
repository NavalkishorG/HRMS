from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import RoleName
from app.core.exceptions import DomainError, ForbiddenError, NotFoundError
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.employee import Employee
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.schemas.common import UserLoginRequest, UserRegisterRequest


def _get_role(db: Session, role_name: str) -> Role:
    role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
    if role is None:
        raise DomainError('role_not_found', f'Role {role_name} not found')
    return role


def register_user(db: Session, payload: UserRegisterRequest) -> dict:
    if payload.role != RoleName.EMPLOYEE.value:
        raise ForbiddenError('Public registration is only allowed for Employee role')

    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise DomainError('email_exists', 'Email already registered', 409)

    role = _get_role(db, payload.role)
    user = User(email=payload.email, password_hash=hash_password(payload.password), role_id=role.id)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError('email_exists', 'Email already registered', 409) from exc
    db.refresh(user)
    return {'id': user.id, 'email': user.email, 'role': role.name}


def login_user(db: Session, payload: UserLoginRequest) -> dict:
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise DomainError('invalid_credentials', 'Invalid email or password', 401)

    role = db.execute(select(Role).where(Role.id == user.role_id)).scalar_one()
    access_token = create_access_token(str(user.id), role.name)
    refresh_token, expires_at = create_refresh_token(str(user.id), role.name)

    db.add(RefreshToken(user_id=user.id, token=refresh_token, expires_at=expires_at))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError('token_persist_failed', 'Could not persist refresh token', 409) from exc

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


def refresh_access_token(db: Session, token: str) -> dict:
    data = decode_token(token)
    if data.get('type') != 'refresh':
        raise DomainError('invalid_token', 'Invalid token type', 401)

    token_row = db.execute(select(RefreshToken).where(RefreshToken.token == token)).scalar_one_or_none()
    if token_row is None or token_row.revoked_at is not None or token_row.expires_at < datetime.now(timezone.utc):
        raise DomainError('invalid_refresh_token', 'Refresh token is invalid or expired', 401)

    user = db.execute(select(User).where(User.id == int(data['sub']))).scalar_one_or_none()
    if user is None:
        raise NotFoundError('User not found')

    role = db.execute(select(Role).where(Role.id == user.role_id)).scalar_one()
    access_token = create_access_token(str(user.id), role.name)
    return {'access_token': access_token, 'refresh_token': token, 'token_type': 'bearer'}


def logout_user(db: Session, token: str) -> dict:
    token_row = db.execute(select(RefreshToken).where(RefreshToken.token == token)).scalar_one_or_none()
    if token_row is None:
        return {'message': 'Logged out'}

    token_row.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return {'message': 'Logged out'}


def enforce_delete_rule(actor_role: str, target_user_role: str) -> None:
    if actor_role == RoleName.HR.value and target_user_role == RoleName.ADMIN.value:
        raise ForbiddenError('HR cannot delete Admin')
