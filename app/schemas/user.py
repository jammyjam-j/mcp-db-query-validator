from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    birth_date: Optional[date]
    is_active: bool = True

    @validator("username")
    def username_cannot_be_empty(cls, v):
        if not v.strip():
            raise ValueError("username must not be empty or whitespace")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @validator("password")
    def password_strength(cls, v):
        if any(c.isdigit() for c in v) and any(c.isalpha() for c in v):
            return v
        raise ValueError("Password must contain both letters and numbers")


class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    full_name: Optional[str] = Field(None, max_length=100)
    birth_date: Optional[date]
    is_active: Optional[bool]

    @validator("*")
    def not_empty(cls, v, field):
        if isinstance(v, str) and not v.strip():
            raise ValueError(f"{field.name} must not be empty or whitespace")
        return v


class UserInDB(UserBase):
    id: int
    hashed_password: str

    class Config:
        orm_mode = True


class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True

        from_orm = True

        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
        }