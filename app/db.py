import os
from typing import Generator

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from fastapi import Depends, HTTPException, status

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    db: Session | None = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()

class DBError(Exception):
    pass

def execute_sql(sql: str, params: dict | None = None) -> list[dict]:
    try:
        with engine.connect() as connection:
            result = connection.execute(
                sql,
                params or {},
            )
            return [dict(row) for row in result]
    except Exception as exc:
        raise DBError(f"SQL execution failed: {exc}") from exc

def fetch_one(sql: str, params: dict | None = None) -> dict | None:
    rows = execute_sql(sql, params)
    return rows[0] if rows else None

def fetch_all(sql: str, params: dict | None = None) -> list[dict]:
    return execute_sql(sql, params)

def commit_transaction(session: Session) -> None:
    try:
        session.commit()
    except Exception as exc:
        session.rollback()
        raise DBError(f"Transaction commit failed: {exc}") from exc

def rollback_transaction(session: Session) -> None:
    try:
        session.rollback()
    except Exception as exc:
        raise DBError(f"Transaction rollback failed: {exc}") from exc

def close_session(session: Session) -> None:
    if session.is_active:
        session.close()