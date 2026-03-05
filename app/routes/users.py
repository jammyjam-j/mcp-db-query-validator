from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User as DBUser
from app.schemas.user import (
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.serializers.user_serializer import (
    serialize_user,
    serialize_users,
)
from app.services.query_validator import QueryValidator

router = APIRouter(prefix="/users", tags=["users"])


def validate_query(query: str) -> None:
    validator = QueryValidator()
    if not validator.is_safe(query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query contains unsafe operations",
        )


@router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    users = db.query(DBUser).all()
    return serialize_users(users)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    validate_query(user_in.password)
    new_user = DBUser(
        username=user_in.username,
        email=user_in.email,
        hashed_password=user_in.password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return serialize_user(new_user)


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return serialize_user(user)


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user_in.username is not None:
        user.username = user_in.username
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.password is not None:
        validate_query(user_in.password)
        user.hashed_password = user_in.password
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    db.delete(user)
    db.commit()
    return None