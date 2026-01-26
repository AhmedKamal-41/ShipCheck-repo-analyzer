import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repo_url: Mapped[str] = mapped_column(Text, nullable=False)
    repo_owner: Mapped[str | None] = mapped_column(Text, nullable=True)
    repo_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(Text, nullable=True)  # pending | done | failed
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    findings_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
