from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import user as user_crud
from app.dependencies import get_barber_user, get_current_user, get_db
from app.models.user import User
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate, UserUpdate
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["users"])


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    """
    logger.info(f"Creating new user with email: {user.email}")

    # Check if email already exists
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        logger.warning(f"User with email {user.email} already exists")
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username already exists
    db_user = user_crud.get_user_by_username(db, username=user.username)
    if db_user:
        logger.warning(f"User with username {user.username} already exists")
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create new user
    user = user_crud.create_user(db=db, user=user)
    logger.info(f"Created user with ID: {user.id}")
    return user


@router.get("/", response_model=List[UserSchema])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve users.
    """
    logger.info(f"Getting users list (skip={skip}, limit={limit})")
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user.
    """
    logger.info(f"Getting current user info for user ID: {current_user.id}")
    return current_user


@router.get("/{user_id}", response_model=UserSchema)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific user by id.
    """
    logger.info(f"Getting user with ID: {user_id}")
    db_user = user_crud.get_user(db, user_id=user_id)
    if db_user is None:
        logger.warning(f"User with ID {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a user.
    """
    logger.info(f"Updating user with ID: {user_id}")

    # Check if user exists
    db_user = user_crud.get_user(db, user_id=user_id)
    if db_user is None:
        logger.warning(f"User with ID {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")

    # Check permissions (only allow users to update their own profile unless they are barbers)
    if current_user.id != user_id and not current_user.is_barber:
        logger.warning(
            f"User {current_user.id} attempted to update user {user_id} without permission"
        )
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Update user
    updated_user = user_crud.update_user(db=db, user_id=user_id, user=user)
    logger.info(f"Updated user with ID: {user_id}")
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_barber_user),
):
    """
    Delete a user.
    """
    logger.info(f"Deleting user with ID: {user_id}")

    # Only barbers can delete users
    success = user_crud.delete_user(db=db, user_id=user_id)
    if not success:
        logger.warning(f"User with ID {user_id} not found for deletion")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"Deleted user with ID: {user_id}")
    return None


@router.get("/barbers/", response_model=List[UserSchema])
def read_barbers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all barbers.
    """
    logger.info(f"Getting barbers list (skip={skip}, limit={limit})")
    barbers = user_crud.get_barbers(db, skip=skip, limit=limit)
    return barbers
