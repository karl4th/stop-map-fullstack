"""add production query indexes

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-25 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_stop_cards_status_created_at", "stop_cards", ["status", "created_at"])
    op.create_index("ix_stop_cards_section_status_created_at", "stop_cards", ["section_id", "status", "created_at"])
    op.create_index("ix_stop_cards_violator_status_created_at", "stop_cards", ["violator_id", "status", "created_at"])
    op.create_index("ix_stop_cards_reporter_created_at", "stop_cards", ["reporter_id", "created_at"])
    op.create_index("ix_stop_card_photos_minio_key", "stop_card_photos", ["minio_key"])
    op.create_index("ix_users_role_status", "users", ["role", "status"])
    op.create_index("ix_users_section_status", "users", ["section_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_users_section_status", table_name="users")
    op.drop_index("ix_users_role_status", table_name="users")
    op.drop_index("ix_stop_card_photos_minio_key", table_name="stop_card_photos")
    op.drop_index("ix_stop_cards_reporter_created_at", table_name="stop_cards")
    op.drop_index("ix_stop_cards_violator_status_created_at", table_name="stop_cards")
    op.drop_index("ix_stop_cards_section_status_created_at", table_name="stop_cards")
    op.drop_index("ix_stop_cards_status_created_at", table_name="stop_cards")
