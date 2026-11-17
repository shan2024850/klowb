"""Append-only audit log table (docs/security.md section 2.10).

Rows are only ever inserted. The application database role is restricted to
INSERT/SELECT on this table when least-privilege roles land (Phase 11/15).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Identity, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from libs.storage.base import Base


class AuditLogRow(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    subject: Mapped[str | None] = mapped_column(String(128))
    outcome: Mapped[str] = mapped_column(String(32))
    correlation_id: Mapped[str | None] = mapped_column(String(128))
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        Index("ix_audit_log_occurred_at", "occurred_at"),
        Index("ix_audit_log_action", "action"),
    )
