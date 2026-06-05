"""new_workflow: roles, statuses, stop_card audit fields, photo_type

Revision ID: a1b2c3d4e5f6
Revises: 5988b21e385c
Create Date: 2026-06-05 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "5988b21e385c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Новая роль safety_engineer
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'safety_engineer'")

    # 2. Заменяем enum stopcard_status: сначала в VARCHAR, затем пересоздаём
    op.execute("ALTER TABLE stop_cards ALTER COLUMN status TYPE VARCHAR USING status::text")
    op.execute("DROP TYPE IF EXISTS stopcard_status")
    op.execute(
        "CREATE TYPE stopcard_status AS ENUM "
        "('created','under_review','in_progress','safety_check','approved','rejected','closed')"
    )
    # Мигрируем старые значения
    op.execute("UPDATE stop_cards SET status = 'created'      WHERE status = 'issued'")
    op.execute("UPDATE stop_cards SET status = 'under_review' WHERE status = 'acknowledged'")
    op.execute("UPDATE stop_cards SET status = 'approved'     WHERE status = 'closed'")
    op.execute("UPDATE stop_cards SET status = 'rejected'     WHERE status = 'disputed'")
    op.execute(
        "ALTER TABLE stop_cards ALTER COLUMN status TYPE stopcard_status "
        "USING status::stopcard_status"
    )

    # 3. Новые колонки на stop_cards
    op.add_column("stop_cards", sa.Column("acknowledged_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("stop_cards", sa.Column("acknowledged_at", sa.DateTime(), nullable=True))
    op.add_column("stop_cards", sa.Column("fix_description", sa.Text(), nullable=True))
    op.add_column("stop_cards", sa.Column("fixed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("stop_cards", sa.Column("fixed_at", sa.DateTime(), nullable=True))
    op.add_column("stop_cards", sa.Column("safety_note", sa.Text(), nullable=True))
    op.add_column("stop_cards", sa.Column("safety_checked_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("stop_cards", sa.Column("safety_checked_at", sa.DateTime(), nullable=True))
    op.add_column("stop_cards", sa.Column("closed_at", sa.DateTime(), nullable=True))

    # Удаляем старое поле dispute_reason если есть
    op.execute(
        "ALTER TABLE stop_cards DROP COLUMN IF EXISTS dispute_reason"
    )

    # 4. Поле photo_type в stop_card_photos
    op.add_column(
        "stop_card_photos",
        sa.Column("photo_type", sa.String(10), nullable=False, server_default="before"),
    )


def downgrade() -> None:
    op.drop_column("stop_card_photos", "photo_type")

    op.drop_column("stop_cards", "closed_at")
    op.drop_column("stop_cards", "safety_checked_at")
    op.drop_column("stop_cards", "safety_checked_by_id")
    op.drop_column("stop_cards", "safety_note")
    op.drop_column("stop_cards", "fixed_at")
    op.drop_column("stop_cards", "fixed_by_id")
    op.drop_column("stop_cards", "fix_description")
    op.drop_column("stop_cards", "acknowledged_at")
    op.drop_column("stop_cards", "acknowledged_by_id")
    op.add_column("stop_cards", sa.Column("dispute_reason", sa.Text(), nullable=True))

    op.execute("ALTER TABLE stop_cards ALTER COLUMN status TYPE VARCHAR USING status::text")
    op.execute("DROP TYPE IF EXISTS stopcard_status")
    op.execute(
        "CREATE TYPE stopcard_status AS ENUM ('issued','acknowledged','closed','disputed')"
    )
    op.execute("UPDATE stop_cards SET status = 'issued'       WHERE status = 'created'")
    op.execute("UPDATE stop_cards SET status = 'acknowledged' WHERE status = 'under_review'")
    op.execute("UPDATE stop_cards SET status = 'closed'       WHERE status = 'approved'")
    op.execute("UPDATE stop_cards SET status = 'disputed'     WHERE status = 'rejected'")
    op.execute(
        "ALTER TABLE stop_cards ALTER COLUMN status TYPE stopcard_status "
        "USING status::stopcard_status"
    )
