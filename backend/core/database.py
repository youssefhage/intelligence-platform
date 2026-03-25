from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings

engine = create_async_engine(settings.database_url, echo=settings.app_env == "development")
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Redis client (lazy-initialized)
_redis_client: Redis | None = None


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client
