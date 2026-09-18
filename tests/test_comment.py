import pytest
from fastapi import status
from httpx2 import AsyncClient

from .conftest import auth_headers, create_and_login_user  # noqa


@pytest.mark.asyncio
async def test_create_comment(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa
):
    response = await client.post(
        "/posts",
        json={
            "title": "New Post",
            "content": "New Post Content",
        },
        headers=auth_headers,
    )
    post_id = response.json()["id"]
    response = await client.post(
        f"/posts/{post_id}/comments",
        json={"content": "This is a test comment."},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "This is a test comment."
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_comments(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa
):
    response = await client.post(
        "/posts",
        json={
            "title": "New Post",
            "content": "New Post Content",
        },
        headers=auth_headers,
    )
    post_id = response.json()["id"]
    await client.post(
        f"/posts/{post_id}/comments",
        json={"content": "This is a test comment."},
        headers=auth_headers,
    )
    response = await client.get(f"/posts/{post_id}/comments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["content"] == "This is a test comment."


@pytest.mark.asyncio
async def test_update_comment(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa
):
    response = await client.post(
        "/posts",
        json={
            "title": "New Post",
            "content": "New Post Content",
        },
        headers=auth_headers,
    )
    post_id = response.json()["id"]
    response = await client.post(
        f"/posts/{post_id}/comments",
        json={"content": "This is a test comment."},
        headers=auth_headers,
    )
    comment_id = response.json()["id"]
    response = await client.patch(
        f"/posts/{post_id}/comments/{comment_id}",
        json={"content": "Updated comment content."},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated comment content."


@pytest.mark.asyncio
async def test_delete_comment(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa
):
    response = await client.post(
        "/posts",
        json={
            "title": "New Post",
            "content": "New Post Content",
        },
        headers=auth_headers,
    )
    post_id = response.json()["id"]
    response = await client.post(
        f"/posts/{post_id}/comments",
        json={"content": "This is a test comment."},
        headers=auth_headers,
    )
    comment_id = response.json()["id"]
    response = await client.delete(
        f"/posts/{post_id}/comments/{comment_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_comment_requires_auth(client: AsyncClient):
    response = await client.post(
        "/posts/1/comments",
        json={
            "content": "New Comment",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_user_cannot_update_other_users_comment(
    client: AsyncClient,
):
    owner_token = await create_and_login_user(
        client,
        "comment-owner",
        "owner@example.com",
    )

    other_token = await create_and_login_user(
        client,
        "other-user",
        "other@example.com",
    )

    post_response = await client.post(
        "/posts",
        json={
            "title": "Ownership Post",
            "content": "Content",
        },
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
    )

    post_id = post_response.json()["id"]

    comment_response = await client.post(
        f"/posts/{post_id}/comments",
        json={
            "content": "Owner comment",
        },
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
    )

    comment_id = comment_response.json()["id"]

    response = await client.patch(
        f"posts/{post_id}/comments/{comment_id}",
        json={
            "content": "Hacked comment",
        },
        headers={
            "Authorization": f"Bearer {other_token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have permission for this action."


@pytest.mark.asyncio
async def test_update_own_comment(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa
):

    post_response = await client.post(
        "/posts",
        json={
            "title": "Update Post",
            "content": "Content",
        },
        headers=auth_headers,
    )

    post_id = post_response.json()["id"]

    comment_response = await client.post(
        f"/posts/{post_id}/comments",
        json={
            "content": "Original comment",
        },
        headers=auth_headers,
    )

    comment_id = comment_response.json()["id"]

    response = await client.patch(
        f"/posts/{post_id}/comments/{comment_id}",
        json={
            "content": "Updated comment",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated comment"


@pytest.mark.asyncio
async def test_create_comment_for_nonexistent_post(
    client: AsyncClient,
):
    token = await create_and_login_user(
        client,
        "missing-post-user",
        "missing-post@example.com",
    )
    post_id: int = 999999
    response = await client.post(
        f"/posts/{post_id}/comments",
        json={
            "content": "This should fail",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == f"Post '{post_id}' not found"


@pytest.mark.asyncio
async def test_delete_own_comment(client: AsyncClient):
    token = await create_and_login_user(
        client,
        "delete-user",
        "delete@example.com",
    )

    post_response = await client.post(
        "/posts",
        json={
            "title": "Delete Post",
            "content": "Content",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    post_id = post_response.json()["id"]

    comment_response = await client.post(
        f"/posts/{post_id}/comments",
        json={
            "content": "Delete me",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    comment_id = comment_response.json()["id"]

    response = await client.delete(
        f"posts/{post_id}/comments/{comment_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 204

    response = await client.get(
        f"/posts/{post_id}/comments",
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_user_cannot_delete_other_users_comment(
    client: AsyncClient,
):
    owner_token = await create_and_login_user(
        client,
        "delete-owner",
        "delete-owner@example.com",
    )

    other_token = await create_and_login_user(
        client,
        "delete-other",
        "delete-other@example.com",
    )

    post_response = await client.post(
        "/posts",
        json={
            "title": "Protected Post",
            "content": "Content",
        },
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
    )

    post_id = post_response.json()["id"]

    comment_response = await client.post(
        f"/posts/{post_id}/comments",
        json={
            "content": "Protected comment",
        },
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
    )

    comment_id = comment_response.json()["id"]

    response = await client.delete(
        f"/posts/{post_id}/comments/{comment_id}",
        headers={
            "Authorization": f"Bearer {other_token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have permission for this action."


@pytest.mark.asyncio
async def test_create_comment_with_empty_content(
    client: AsyncClient,
):
    token = await create_and_login_user(
        client,
        "validation-user",
        "validation@example.com",
    )

    post_response = await client.post(
        "/posts",
        json={
            "title": "Validation Post",
            "content": "Content",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    post_id = post_response.json()["id"]

    response = await client.post(
        f"/posts/{post_id}/comments",
        json={
            "content": "",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422
