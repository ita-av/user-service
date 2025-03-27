from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.crud.user import get_user_by_email
from app.dependencies import get_db
from app.schemas.auth import LoginRequest, Token
from app.utils.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    verify_password,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["authentication"])


@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    logger.info(f"Login attempt for: {form_data.username}")

    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, is_barber=user.is_barber, expires_delta=access_token_expires
    )

    logger.info(f"Successful login for user ID: {user.id}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/email", response_model=Token)
def login_with_email(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password
    """
    logger.info(f"Email login attempt for: {login_data.email}")

    user = get_user_by_email(db, email=login_data.email)
    if not user or not verify_password(login_data.password, user.hashed_password):
        logger.warning(f"Failed email login attempt for: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, is_barber=user.is_barber, expires_delta=access_token_expires
    )

    logger.info(f"Successful email login for user ID: {user.id}")
    return {"access_token": access_token, "token_type": "bearer"}
