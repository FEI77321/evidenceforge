from uuid import UUID

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from evidenceforge.domain.tasks import TaskStatus
from evidenceforge.infrastructure.persistence.base import Base

_STATUS_VALUES = ", ".join(f"'{status.value}'" for status in TaskStatus)


class ResearchTaskRecord(Base):
    """research_tasks 表对应的 PostgreSQL 持久化记录。"""

    __tablename__ = "research_tasks"

    __table_args__ = (
        CheckConstraint(
            f"status IN ({_STATUS_VALUES})",
            name="ck_research_tasks_status_known",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
    )
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
