from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.posts import router as post_router

app = FastAPI(title="FastAPI Blog")


app.include_router(auth_router)
app.include_router(post_router)
