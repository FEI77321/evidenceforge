from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from evidenceforge.infrastructure.config import Settings

settings = Settings()

async_engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """为调用方提供一次数据库会话，并在结束后自动关闭。"""

    async with async_session_factory() as session:
        yield session
