from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """从本地环境变量读取基础设施配置。"""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    fixture_research_source_path: Path = (
        PROJECT_ROOT
        / "backend"
        / "tests"
        / "fixtures"
        / "research_sources"
        / "fastapi_background_tasks.md"
    )

    @property
    def redis_broker_url(self) -> str:
        """构造 Celery 投递任务时使用的 Redis 地址。"""

        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def redis_result_backend_url(self) -> str:
        """构造 Celery 保存任务执行结果时使用的 Redis 地址。"""

        return f"redis://{self.redis_host}:{self.redis_port}/1"

    @property
    def database_url(self) -> URL:
        """构造供 SQLAlchemy 异步引擎使用的数据库地址。"""

        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )
