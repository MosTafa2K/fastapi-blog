import pytest
from fastapi import status
from httpx2 import AsyncClient


@pytest.mark.asyncio
async def test_get_category_list(client: AsyncClient):
    """Test retrieving the list of categories"""
    response = await client.get("/category")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient):
    """Test creating a new category"""
    response = await client.post(
        "/category",
        json={
            "name": "New category",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient):
    """Test updating a category"""
    response = await client.post(
        "/category",
        json={
            "name": "Old category",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    category_id: int = response.json()["id"]

    response = await client.patch(
        f"/category/{category_id}",
        json={
            "name": "Updated category",
        },
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient):
    """Test deleting a category"""
    response = await client.post(
        "/category",
        json={
            "name": "Category to delete",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    category_id: int = response.json()["id"]

    response = await client.delete(f"/category/{category_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
