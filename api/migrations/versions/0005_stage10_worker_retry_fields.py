"""stage10 worker retry fields

Revision ID: 0005_stage10_worker_retry_fields
Revises: 0004_stage9_announcement_channel
Create Date: 2026-03-06 06:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005_stage10_worker_retry_fields"
down_revision: Union[str, Sequence[str], None] = "0004_stage9_announcement_channel"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scheduled_announcements", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("scheduled_announcements", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("scheduled_announcements", "next_attempt_at")
    op.drop_column("scheduled_announcements", "retry_count")
