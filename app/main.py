from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.categories import router as category_router
from app.api.comments import router as comment_router
from app.api.posts import router as post_router

app = FastAPI(
    title="FastAPI Blog",
    description="A simple blog API built with FastAPI and SQLAlchemy",
    version="1.0.0",
)


app.include_router(auth_router)
app.include_router(post_router)
app.include_router(category_router)
app.include_router(comment_router)
