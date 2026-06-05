from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.bootstrap import create_first_admin
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.minio import ensure_bucket
from app.core.redis import close_redis, get_redis
from app.routers.admin import router as admin_router
from app.routers.bot import router as bot_router
from app.routers.manager import router as manager_router
from app.routers.photos import router as photos_router
from app.routers.safety_engineer import router as safety_engineer_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bucket()
    await get_redis()
    async with AsyncSessionLocal() as db:
        await create_first_admin(db)
    yield
    await close_redis()


app = FastAPI(title="StopMap API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router, prefix="/api")
app.include_router(manager_router, prefix="/api")
app.include_router(safety_engineer_router, prefix="/api")
app.include_router(bot_router, prefix="/api")
app.include_router(photos_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
