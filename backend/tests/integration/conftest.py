from collections.abc import AsyncIterator

import pytest

from evidenceforge.infrastructure.database import async_engine


@pytest.fixture(autouse=True)
async def dispose_async_engine_after_test(
    anyio_backend: str,
) -> AsyncIterator[None]:
    """避免 asyncpg 连接跨 pytest 事件循环复用。"""

    yield

    await async_engine.dispose()
