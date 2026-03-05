"""stage9 announcement channel

Revision ID: 0004_stage9_announcement_channel
Revises: 0003_stage7_verification_tables
Create Date: 2026-03-06 05:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_stage9_announcement_channel"
down_revision: Union[str, Sequence[str], None] = "0003_stage7_verification_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scheduled_announcements", sa.Column("channel_discord_id", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("scheduled_announcements", "channel_discord_id")
