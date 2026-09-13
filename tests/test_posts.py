import pytest
from fastapi import status
from httpx2 import AsyncClient

from .conftest import auth_headers  # noqa


@pytest.mark.asyncio
async def test_create_post_no_authentication(
    client: AsyncClient,
):
    """Test that creating a post requires authentication."""
    response = await client.post(
        "/posts",
        json={
            "title": "My Post",
            "content": "Hello",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_create_post_requires_authentication(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa
):
    """Test create post endpoint requires authentication."""
    response = await client.post(
        "/posts",
        json={
            "title": "My Post",
            "content": "Hello",
        },
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "My Post"
    assert data["content"] == "Hello"


@pytest.mark.asyncio
async def test_get_post_by_id(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa
):
    """Test retrieve a post using id"""
    response = await client.post(
        "/posts",
        json={
            "title": "My Post1",
            "content": "Hello",
        },
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED

    post_id: int = response.json()["id"]

    response = await client.get(f"/posts/{post_id}")
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["title"] == "My Post1"
    assert data["content"] == "Hello"
    assert data["id"] == post_id


@pytest.mark.asyncio
async def test_update_post(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa
):
    post_response = await client.post(
        "/posts",
        json={
            "title": "Old title",
            "content": "Old content at here",
        },
        headers=auth_headers,
    )
    assert post_response.status_code == status.HTTP_201_CREATED

    post_id: int = post_response.json()["id"]

    update_post_response = await client.patch(
        f"/posts/{post_id}",
        json={
            "title": "New title",
        },
        headers=auth_headers,
    )
    assert update_post_response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_user_cannot_update_other_users_post(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa
):
    create_post_response = await client.post(
        "/posts",
        json={
            "title": "Original title",
            "content": "Original content",
        },
        headers=auth_headers,
    )
    assert create_post_response.status_code == status.HTTP_201_CREATED

    post_id: int = create_post_response.json()["id"]

    await client.post(
        "/auth/register",
        json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "strong-password",
        },
    )
    login_response = await client.post(
        "/auth/login",
        data={
            "username": "user2",
            "password": "strong-password",
        },
    )
    user2_token = login_response.json()["access_token"]

    update_post_response = await client.patch(
        f"/posts/{post_id}",
        json={"title": "Edited title"},
        headers={"Authorization": f"Bearer {user2_token}"},
    )
    assert update_post_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_user_cannot_delete_other_users_post(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa
):
    create_post_response = await client.post(
        "/posts",
        json={
            "title": "Post to delete",
            "content": "Post to delete content",
        },
        headers=auth_headers,
    )
    assert create_post_response.status_code == status.HTTP_201_CREATED

    post_id: int = create_post_response.json()["id"]

    await client.post(
        "/auth/register",
        json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "strong-password",
        },
    )
    login_response = await client.post(
        "/auth/login",
        data={
            "username": "user2",
            "password": "strong-password",
        },
    )
    user2_token = login_response.json()["access_token"]

    update_post_response = await client.delete(
        f"/posts/{post_id}",
        headers={"Authorization": f"Bearer {user2_token}"},
    )
    assert update_post_response.status_code == status.HTTP_403_FORBIDDEN
