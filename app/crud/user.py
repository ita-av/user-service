from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.auth import get_password_hash


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by username."""
    return db.query(User).filter(User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get a list of users."""
    return db.query(User).offset(skip).limit(limit).all()


def get_barbers(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get a list of barbers."""
    return db.query(User).filter(User.is_barber).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user."""
    db_user = User(
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        hashed_password=get_password_hash(user.password),
        is_barber=user.is_barber,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user: UserUpdate) -> Optional[User]:
    """Update an existing user."""
    db_user = get_user(db, user_id)
    if db_user is None:
        return None

    # Convert Pydantic model to dict, excluding unset fields
    update_data = user.dict(exclude_unset=True)

    # Hash password if it's provided
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    # Update user attributes
    for field, value in update_data.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user."""
    db_user = get_user(db, user_id)
    if db_user is None:
        return False

    db.delete(db_user)
    db.commit()
    return True
