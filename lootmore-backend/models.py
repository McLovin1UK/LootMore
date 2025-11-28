import os
from datetime import date

from sqlalchemy import Column, Date, Integer, String

from database import Base

DAILY_QUOTA_DEFAULT = int(os.getenv("DAILY_QUOTA_DEFAULT", "200"))


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True)
    token_hash = Column(String, unique=True, nullable=False)
    daily_quota = Column(Integer, default=DAILY_QUOTA_DEFAULT)
    used_today = Column(Integer, default=0)
    last_reset_at = Column(Date, default=date.today)


def reset_quota_if_needed(token: "ApiToken") -> None:
    if token.last_reset_at is None or token.last_reset_at < date.today():
        token.used_today = 0
        token.last_reset_at = date.today()
