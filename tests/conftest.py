We don't have content of files; assume config has DATABASE_URL maybe to postgres. We'll use SQLite in-memory for tests: override dependency for db session via app.db.get_session or similar. Provide fixture client that overrides dependencies.

Also seed data fixture. Use pytest. Ensure integration with query_validator.

Implement function get_test_client returning TestClient.

Use contextmanager to create temporary database file.

Let's craft generic.

import os
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import Base, get_db


@pytest.fixture(scope="session")
def temp_dir():
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture(scope="session")
def test_database_url(temp_dir):
    db_file = os.path.join(temp_dir, "test.sqlite")
    return f"sqlite:///{db_file}"


@pytest.fixture(scope="session")
def engine(test_database_url):
    engine_ = create_engine(test_database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine_)
    yield engine_
    engine_.dispose()
    os.remove(engine_.url.database)


@pytest.fixture(scope="session")
def SessionLocal(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session(SessionLocal):
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def seed_users(db_session):
    from app.models.user import User

    users = [
        User(username="alice", email="alice@example.com"),
        User(username="bob", email="bob@example.com"),
    ]
    db_session.bulk_save_objects(users)
    db_session.commit()
    return users


@pytest.fixture
def authenticated_client(client, seed_users):
    def get_token(user):
        return f"Bearer test-token-{user.username}"

    original_post = client.post

    def post(url, *args, **kwargs):
        headers = kwargs.pop("headers", {})
        if url == "/login":
            username = kwargs["json"]["username"]
            user = next((u for u in seed_users if u.username == username), None)
            if not user:
                return original_post(url, *args, **kwargs)
            token = get_token(user)
            return pytest.MonkeyPatch().setattr(client, "headers", {"Authorization": token})

        return original_post(url, *args, headers=headers, **kwargs)

    client.post = post
    return client


@pytest.fixture(scope="function")
def reset_database(engine):
    connection = engine.connect()
    transaction = connection.begin()
    yield
    transaction.rollback()
    connection.close()