import asyncio
from datetime import datetime

from app.config import settings
from app.db import get_async_session
from app.models.user import User
from sqlalchemy.exc import SQLAlchemyError


async def create_sample_users(session):
    sample_data = [
        {"username": "alice", "email": "alice@example.com"},
        {"username": "bob", "email": "bob@example.com"},
        {"username": "carol", "email": "carol@example.com"},
    ]
    users = []
    for data in sample_data:
        user = User(**data, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        session.add(user)
        users.append(user)
    try:
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        raise RuntimeError(f"Failed to insert sample users: {exc}") from exc
    return users


async def seed():
    async with get_async_session() as session:
        existing = await session.execute(
            User.__table__.select().limit(1)
        )
        if existing.first():
            print("Sample data already present, skipping seeding.")
            return
        users = await create_sample_users(session)
        print(f"Inserted {len(users)} sample users.")


if __name__ == "__main__":
    asyncio.run(seed())