import os
from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base

DAILY_QUOTA_DEFAULT = int(os.getenv("DAILY_QUOTA_DEFAULT", "200"))


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True)
    token_hash = Column(String, unique=True, nullable=False)
    daily_quota = Column(Integer, default=DAILY_QUOTA_DEFAULT)
    used_today = Column(Integer, default=0)
    last_reset_at = Column(Date, default=date.today)

    logs = relationship("ApiUsageLog", back_populates="token", cascade="all, delete-orphan")


class ApiUsageLog(Base):
    __tablename__ = "api_usage_logs"

    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey("api_tokens.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    request_ip = Column(String(64))
    latency_ms = Column(Integer)
    text_length = Column(Integer)
    success = Column(Boolean, default=False, nullable=False)

    token = relationship("ApiToken", back_populates="logs")


def reset_quota_if_needed(token: "ApiToken") -> None:
    if token.last_reset_at is None or token.last_reset_at < date.today():
        token.used_today = 0
        token.last_reset_at = date.today()
