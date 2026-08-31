import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection

from evidenceforge.infrastructure.config import Settings
from evidenceforge.infrastructure.database import async_engine
from evidenceforge.infrastructure.persistence import models  # noqa: F401
from evidenceforge.infrastructure.persistence.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = Settings()
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url.render_as_string(hide_password=False),
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """生成 SQL 文本，但不连接真实数据库。"""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """在同步连接包装器中执行迁移逻辑。"""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """通过项目的异步 Engine 运行迁移。"""

    async with async_engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await async_engine.dispose()


def run_migrations_online() -> None:
    """连接真实数据库并执行迁移。"""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
