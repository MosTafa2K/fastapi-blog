import pytest
from fastapi import status
from httpx2 import AsyncClient

from .conftest import auth_headers  # noqa


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """Test registering a new user."""
    response = await client.post(
        "/auth/register",
        json={
            "username": "mostafa",
            "email": "mostafa@example.com",
            "password": "strong-password",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["username"] == "mostafa"
    assert data["email"] == "mostafa@example.com"

    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient):
    """Test registering a user with a duplicate username or email."""
    payload = {
        "username": "duplicate",
        "email": "duplicate@example.com",
        "password": "strong-password",
    }
    response_1 = await client.post("/auth/register", json=payload)
    response_2 = await client.post("/auth/register", json=payload)
    assert response_1.status_code == status.HTTP_201_CREATED
    assert response_2.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_register_user_with_invalid_data(client: AsyncClient):
    """Test registering a user with invalid data (missing required fields)."""
    payload = {
        "username": "test_user",
        "password": "test_user_password",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    """Test login with a registered user."""
    payload = {
        "username": "login-user",
        "email": "login-user@example.com",
        "password": "login-user-password",
    }
    await client.post(
        "/auth/register",
        json=payload,
    )
    response = await client.post(
        "/auth/login",
        data={
            "username": "login-user",
            "password": "login-user-password",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_user_with_invalid_password(client: AsyncClient):
    """Test login with an invalid password."""
    payload = {
        "username": "valid-user",
        "email": "valid@email.com",
        "password": "user-valid-password",
    }
    await client.post(
        "/auth/register",
        json=payload,
    )
    response = await client.post(
        "/auth/login",
        data={
            "username": "valid-password",
            "password": "user-invalid-password",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_login_unregistered_user(client: AsyncClient):
    """Test login in with an unregistered user."""
    response = await client.post(
        "/auth/login",
        data={
            "username": "unregistered-user",
            "password": "unregistered-user-password",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_register_with_logged_in_user(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa: F811
):
    """Test that a logged-in user cannot register a new user."""
    register_response = await client.post(
        "/auth/register",
        json={
            "username": "user2",
            "password": "user2password",
            "email": "user2@email.com",
        },
        headers=auth_headers,
    )
    assert register_response.status_code == status.HTTP_403_FORBIDDEN
