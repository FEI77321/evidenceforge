import pytest
from sqlalchemy import text

from evidenceforge.infrastructure.database import async_engine


@pytest.mark.anyio
async def test_database_connection() -> None:
    async with async_engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))

    assert result.scalar_one() == 1
