from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# Base user schema with shared attributes
class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_barber: bool = False


# Schema for user creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


# Schema for user updates
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_barber: Optional[bool] = None


# Schema for user responses
class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
