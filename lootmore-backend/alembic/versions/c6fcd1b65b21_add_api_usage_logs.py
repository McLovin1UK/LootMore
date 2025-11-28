"""add api usage log table

Revision ID: c6fcd1b65b21
Revises: 8a4bffb0c1f4
Create Date: 2024-11-28 22:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c6fcd1b65b21"
down_revision: Union[str, None] = "8a4bffb0c1f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_usage_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("token_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("request_ip", sa.String(length=64), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("text_length", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["token_id"], ["api_tokens.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("api_usage_logs")
