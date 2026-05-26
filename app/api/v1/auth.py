from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import RefreshRequest, TokenResponse, UserLoginRequest, UserRegisterRequest
from app.services.auth_service import login_user, logout_user, refresh_access_token, register_user


router = APIRouter()


@router.post('/register')
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    return register_user(db, payload)


@router.post('/login', response_model=TokenResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    return login_user(db, payload)


@router.post('/refresh', response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return refresh_access_token(db, payload.refresh_token)


@router.post('/logout')
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    return logout_user(db, payload.refresh_token)
