from pydantic import BaseModel, EmailStr


# Token response schema
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Login request schema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
