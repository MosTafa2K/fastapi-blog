from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.exceptions import CategoryNotFound, PostNotFound
from app.models.category import Category
from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate, PostResponse, PostUpdate

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("", response_model=list[PostResponse], status_code=status.HTTP_200_OK)
async def list_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=0)] = 10,
    skip: Annotated[int, Query(ge=0, le=100)] = 0,
    category_id: int | None = None,
):
    """List all posts with pagination."""
    query = select(Post)
    if category_id:
        query = query.where(Post.category_id == category_id)
    query = query.order_by(Post.created_at.desc()).limit(limit).offset(skip)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def create_post(
    data: PostCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new post."""
    if data.category_id:
        result = await db.execute(
            select(Category).where(Category.id == data.category_id)
        )
        category = result.scalar_one_or_none()
        if not category:
            raise CategoryNotFound(data.category_id)

    post = Post(
        title=data.title,
        slug=data.title.lower().replace(" ", "-"),
        content=data.content,
        category_id=data.category_id,
        author_id=current_user.id,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    """Get a post by its ID."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post: Post | None = result.scalar_one_or_none()
    print(post)
    if post is None:
        raise PostNotFound(post_id)
    return post


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    data: PostUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a post by its ID. Only the author of the post can update it."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post: Post | None = result.scalar_one_or_none()
    if post is None:
        raise PostNotFound(post_id)
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not author of this post!",
        )
    update_data = data.model_dump(exclude_none=True, exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)
    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a post by its ID. Only the author of the post can delete it."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post: Post | None = result.scalar_one_or_none()
    if post is None:
        raise PostNotFound(post_id)
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not author of this post!",
        )
    await db.delete(post)
    await db.commit()
