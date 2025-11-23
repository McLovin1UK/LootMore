import uuid
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=True)
    display_name = Column(String, nullable=True)

    token_hash = Column(String, unique=True, nullable=False)
    tier = Column(String, nullable=False, default="alpha")   # alpha/founder/standard/banned
    is_active = Column(Boolean, nullable=False, default=True)

    daily_quota = Column(Integer, nullable=False, default=200)
    used_today = Column(Integer, nullable=False, default=0)
    quota_reset_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    game = Column(String, nullable=True)
    client_version = Column(String, nullable=True)

    request_ts = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    latency_ms = Column(Integer, nullable=True)

    status = Column(String, nullable=False)  # ok/unauthorized/error/over_quota
    error_code = Column(String, nullable=True)
    error_msg = Column(Text, nullable=True)

    callout_text = Column(Text, nullable=True)
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
