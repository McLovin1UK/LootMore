"""initial token table

Revision ID: 8a4bffb0c1f4
Revises: 
Create Date: 2024-11-28 22:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8a4bffb0c1f4"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("daily_quota", sa.Integer(), server_default=sa.text("200"), nullable=True),
        sa.Column("used_today", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("last_reset_at", sa.Date(), nullable=True),
        sa.UniqueConstraint("token_hash"),
    )


def downgrade() -> None:
    op.drop_table("api_tokens")
