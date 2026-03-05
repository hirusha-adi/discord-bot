"""stage2 auth columns

Revision ID: 0002_stage2_auth_columns
Revises: 0001_stage1_core_models
Create Date: 2026-03-06 01:35:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_stage2_auth_columns"
down_revision: Union[str, Sequence[str], None] = "0001_stage1_core_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("discord_access_token", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("discord_token_scope", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("discord_token_expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "discord_token_expires_at")
    op.drop_column("users", "discord_token_scope")
    op.drop_column("users", "discord_access_token")
