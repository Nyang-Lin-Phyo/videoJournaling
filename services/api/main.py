
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import initialize_database
from .routes.journals import router as journals_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Video Journaling API",
    description="Local backend for the AI video journaling platform.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(journals_router)
