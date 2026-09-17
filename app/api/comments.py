from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import required_current_user
from app.exceptions import CommentNotFound, PermissionDenied, PostNotFound
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comments import CommentCreate, CommentResponse, CommentUpdate

router = APIRouter(
    prefix="/posts/{post_id}/comments",
    tags=["Comments"],
)


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    data: CommentCreate,
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(required_current_user)],
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post: Post | None = result.scalar_one_or_none()
    if post is None:
        raise PostNotFound(post_id)
    comment = Comment(
        content=data.content,
        author_id=current_user.id,
        post_id=post.id,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(post)

    return comment


@router.get("", response_model=list[CommentResponse])
async def list_comments(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(
            Comment.created_at.desc(),
        )
    )
    return result.scalars().all()


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    post_id: int,
    comment_id: int,
    data: CommentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(required_current_user)],
):
    query = await db.execute(
        select(Comment).where(
            Comment.id == comment_id,
            Post.id == post_id,
        )
    )
    comment = query.scalar_one_or_none()
    if comment is None:
        raise CommentNotFound(comment_id)
    if comment.author_id != current_user.id:
        raise PermissionDenied()
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)
    await db.commit()
    await db.refresh(comment)

    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    post_id: int,
    comment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(required_current_user)],
):
    query = await db.execute(
        select(Comment).where(
            Comment.id == comment_id,
            Post.id == post_id,
        )
    )
    comment = query.scalar_one_or_none()
    if comment is None:
        raise CommentNotFound(comment_id)
    if comment.author_id != current_user.id:
        raise PermissionDenied()
    await db.delete(comment)
    await db.commit()
