import os

import pytest_asyncio
from fastapi import status
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/blog_test",
)


test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)


TestSessionLocal = async_sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,
    join_transaction_mode="create_savepoint",
)


@pytest_asyncio.fixture(
    scope="session",
    autouse=True,
)
async def setup_database():
    """
    Create a completely clean database for the test session.
    """
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    """
    Provide an isolated database session for each test.

    Every test runs inside its own transaction.
    The transaction is rolled back after the test,
    so test data cannot leak into other tests.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()

    session = TestSessionLocal(bind=connection)

    try:
        yield session

    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session):
    """
    Async HTTP client using the test database session.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """
    Register and login a test user and return authorization headers.
    """

    response = await client.post(
        "/auth/register",
        json={
            "username": "user1",
            "password": "user1password",
            "email": "user1@email.com",
        },
    )

    response = await client.post(
        "/auth/login",
        data={
            "username": "user1",
            "password": "user1password",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


async def create_and_login_user(
    client: AsyncClient,
    username: str,
    email: str,
    password: str | None = None,
):
    user_password = f"{username}password" if password is None else password
    await client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": user_password,
        },
    )
    response = await client.post(
        "/auth/login",
        data={
            "username": username,
            "password": user_password,
        },
    )
    return response.json()["access_token"]
