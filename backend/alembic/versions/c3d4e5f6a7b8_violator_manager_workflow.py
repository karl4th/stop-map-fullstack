"""violator manager workflow

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-19 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("stop_cards", sa.Column("manager_note", sa.Text(), nullable=True))
    op.add_column("stop_cards", sa.Column("manager_checked_by_id", sa.Integer(), nullable=True))
    op.add_column("stop_cards", sa.Column("manager_checked_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_stop_cards_manager_checked_by_id_users",
        "stop_cards",
        "users",
        ["manager_checked_by_id"],
        ["id"],
    )

    op.execute("ALTER TABLE stop_cards ALTER COLUMN status TYPE VARCHAR USING status::text")
    op.execute("UPDATE stop_cards SET status = 'violator_fixing' WHERE status IN ('created', 'under_review', 'in_progress')")
    op.execute("DROP TYPE IF EXISTS stopcard_status")
    op.execute(
        "CREATE TYPE stopcard_status AS ENUM "
        "('created','waiting_violator','violator_fixing','manager_review',"
        "'safety_check','approved','rejected','closed')"
    )
    op.execute(
        "ALTER TABLE stop_cards ALTER COLUMN status TYPE stopcard_status "
        "USING status::stopcard_status"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE stop_cards ALTER COLUMN status TYPE VARCHAR USING status::text")
    op.execute("UPDATE stop_cards SET status = 'created' WHERE status = 'waiting_violator'")
    op.execute("UPDATE stop_cards SET status = 'in_progress' WHERE status IN ('violator_fixing', 'manager_review')")
    op.execute("DROP TYPE IF EXISTS stopcard_status")
    op.execute(
        "CREATE TYPE stopcard_status AS ENUM "
        "('created','under_review','in_progress','safety_check','approved','rejected','closed')"
    )
    op.execute(
        "ALTER TABLE stop_cards ALTER COLUMN status TYPE stopcard_status "
        "USING status::stopcard_status"
    )

    op.drop_constraint("fk_stop_cards_manager_checked_by_id_users", "stop_cards", type_="foreignkey")
    op.drop_column("stop_cards", "manager_checked_at")
    op.drop_column("stop_cards", "manager_checked_by_id")
    op.drop_column("stop_cards", "manager_note")
