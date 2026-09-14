import pytest
from fastapi import status
from httpx2 import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.category import Category
from app.models.post import Post
from app.models.user import User

from .conftest import auth_headers  # noqa


@pytest.mark.asyncio
async def test_list_posts_without_params(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict[str, str],  # noqa
):
    """Test listing posts with default parameters."""
    result = await db_session.execute(select(User).where(User.username == "user1"))
    user = result.scalar_one()

    category = Category(name="Python")
    db_session.add(category)
    await db_session.flush()

    posts = [
        Post(
            title=f"Post {i}",
            slug=f"post-{i}",
            content=f"Content {i}",
            author_id=user.id,
            category_id=category.id,
        )
        for i in range(3)
    ]

    db_session.add_all(posts)
    await db_session.commit()

    response = await client.get(
        "/posts",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3


@pytest.mark.asyncio
async def test_list_posts_with_limit(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict[str, str],  # noqa
):
    """Test listing posts with limit parameter."""
    result = await db_session.execute(select(User).where(User.username == "user1"))
    user = result.scalar_one()

    category = Category(name="Python")
    db_session.add(category)
    await db_session.flush()

    posts = [
        Post(
            title=f"Post {i}",
            slug=f"post-{i}",
            content=f"Content {i}",
            author_id=user.id,
            category_id=category.id,
        )
        for i in range(10)
    ]

    db_session.add_all(posts)
    await db_session.commit()

    response = await client.get(
        "/posts",
        params={"limit": 5},
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert len(data) == 5
    response = await client.get(
        "/posts", params={"limit": 5, "skip": 0, "category_id": 1}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_list_posts_with_category_id(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict[str, str],  # noqa
):
    """Test filtering posts by category_id."""
    result = await db_session.execute(select(User).where(User.username == "user1"))
    user = result.scalar_one()

    python_category = Category(name="Python")
    django_category = Category(name="Django")

    db_session.add_all([python_category, django_category])
    await db_session.flush()

    python_posts = [
        Post(
            title=f"Python Post {i}",
            slug=f"python-post-{i}",
            content=f"Python Content {i}",
            author_id=user.id,
            category_id=python_category.id,
        )
        for i in range(3)
    ]

    django_posts = [
        Post(
            title=f"Django Post {i}",
            slug=f"django-post-{i}",
            content=f"Django Content {i}",
            author_id=user.id,
            category_id=django_category.id,
        )
        for i in range(2)
    ]

    db_session.add_all([*python_posts, *django_posts])
    await db_session.commit()

    response = await client.get(
        "/posts",
        params={"category_id": python_category.id},
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert len(data) == 3

    assert all(post["category_id"] == python_category.id for post in data)


@pytest.mark.asyncio
async def test_list_posts_with_skip(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict[str, str],  # noqa
):
    """Test listing posts with skip parameter."""
    result = await db_session.execute(select(User).where(User.username == "user1"))
    user = result.scalar_one()

    category = Category(name="Python")
    db_session.add(category)
    await db_session.flush()

    posts = [
        Post(
            title=f"Post {i}",
            slug=f"post-{i}",
            content=f"Content {i}",
            author_id=user.id,
            category_id=category.id,
        )
        for i in range(10)
    ]

    db_session.add_all(posts)
    await db_session.commit()

    first_response = await client.get(
        "/posts",
        params={"limit": 5, "skip": 0},
        headers=auth_headers,
    )

    second_response = await client.get(
        "/posts",
        params={"limit": 5, "skip": 5},
        headers=auth_headers,
    )

    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_200_OK

    first_data = first_response.json()
    second_data = second_response.json()

    assert len(first_data) == 5
    assert len(second_data) == 5

    first_ids = {post["id"] for post in first_data}
    second_ids = {post["id"] for post in second_data}

    assert first_ids.isdisjoint(second_ids)


@pytest.mark.asyncio
async def test_list_posts_with_pagination_and_category(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict[str, str],  # noqa
):
    """Test filtering by category_id with pagination."""
    result = await db_session.execute(select(User).where(User.username == "user1"))
    user = result.scalar_one()

    python_category = Category(name="Python")
    django_category = Category(name="Django")

    db_session.add_all([python_category, django_category])
    await db_session.flush()

    python_posts = [
        Post(
            title=f"Python Post {i}",
            slug=f"python-post-{i}",
            content=f"Python Content {i}",
            author_id=user.id,
            category_id=python_category.id,
        )
        for i in range(10)
    ]

    django_post = Post(
        title="Django Post",
        slug="django-post",
        content="Django Content",
        author_id=user.id,
        category_id=django_category.id,
    )

    db_session.add_all([*python_posts, django_post])
    await db_session.commit()

    response = await client.get(
        "/posts",
        params={
            "limit": 5,
            "skip": 0,
            "category_id": python_category.id,
        },
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert len(data) == 5

    assert all(post["category_id"] == python_category.id for post in data)


@pytest.mark.asyncio
async def test_list_posts_ordered_by_created_at_desc(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test that posts are ordered by created_at descending."""
    category = Category(name="Python")
    user = User(
        username="newuser",
        email="newuser@email.com",
        hashed_password=hash_password("newuserpassword"),
    )
    db_session.add(category)
    db_session.add(user)
    await db_session.flush()

    posts = [
        Post(
            title="Old Post",
            content="Old Content",
            slug="post-old",
            category_id=category.id,
            author_id=user.id,
        ),
        Post(
            title="New Post",
            content="New Content",
            slug="post-new",
            category_id=category.id,
            author_id=user.id,
        ),
    ]

    db_session.add_all(posts)
    await db_session.commit()

    response = await client.get("/posts")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert len(data) == 2
    assert data[0]["created_at"] >= data[1]["created_at"]


@pytest.mark.asyncio
async def test_list_posts_invalid_limit(client: AsyncClient):
    """Test that negative limit is rejected."""
    response = await client.get(
        "/posts",
        params={"limit": -1},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_list_posts_invalid_skip(client: AsyncClient):
    """Test that skip greater than 100 is rejected."""
    response = await client.get(
        "/posts",
        params={"skip": 101},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


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
async def test_not_exists_post(client: AsyncClient):
    """Test that retrieving a non-existent post returns a 404 error."""
    response = await client.get("/posts/10000")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_post(
    client: AsyncClient,
    auth_headers: dict[str, str],  # noqa
):
    """Test updating a post with valid authentication and ownership."""
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
    """Test that a user cannot update another user's post."""
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
    """Test that a user cannot delete another user's post."""
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
