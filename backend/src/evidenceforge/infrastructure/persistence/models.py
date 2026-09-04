from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from evidenceforge.domain.tasks import TaskStatus
from evidenceforge.infrastructure.persistence.base import Base

_STATUS_VALUES = ", ".join(f"'{status.value}'" for status in TaskStatus)


class ResearchTaskRecord(Base):
    """research_tasks 表对应的 PostgreSQL 持久化记录。"""

    __tablename__ = "research_tasks"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
    )
    __table_args__ = (
        CheckConstraint(
            f"status IN ({_STATUS_VALUES})",
            name="ck_research_tasks_status_known",
        ),
    )
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )


class SourceSnapshotRecord(Base):
    """source_snapshots 表对应的 PostgreSQL 持久化记录。"""

    __tablename__ = "source_snapshots"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
    )
    task_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "research_tasks.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    source_uri: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source_kind: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    raw_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )