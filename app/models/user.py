from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import validates

from .db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    username: str = Column(String(50), nullable=False)
    email: str = Column(String(255), nullable=False, unique=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} email={self.email!r}>"

    @validates("username")
    def validate_username(self, key: str, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Username must be a string.")
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Username cannot be empty.")
        if len(trimmed) > 50:
            raise ValueError("Username must not exceed 50 characters.")
        return trimmed

    @validates("email")
    def validate_email(self, key: str, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Email must be a string.")
        trimmed = value.strip().lower()
        if not trimmed:
            raise ValueError("Email cannot be empty.")
        if len(trimmed) > 255:
            raise ValueError("Email must not exceed 255 characters.")
        if "@" not in trimmed or "." not in trimmed.split("@")[-1]:
            raise ValueError("Invalid email format.")
        return trimmed

    def to_dict(self) -> dict[str, Optional[object]]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }