from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.posts import router as post_router

app = FastAPI(
    title="FastAPI Blog",
    description="A simple blog API built with FastAPI and SQLAlchemy",
    version="1.0.0",
)


app.include_router(auth_router)
app.include_router(post_router)
