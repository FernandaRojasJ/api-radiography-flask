"""add_patient_identifier_and_require_minimum_fields

Revision ID: e6f4c1a0b9d2
Revises: b5112f27c258
Create Date: 2026-04-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e6f4c1a0b9d2"
down_revision: Union[str, Sequence[str], None] = "b5112f27c258"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("xray_records", schema=None) as batch_op:
        batch_op.add_column(sa.Column("patient_identifier", sa.String(length=50), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE xray_records
            SET patient_identifier = COALESCE(NULLIF(clinical_history_code, ''), 'UNASSIGNED')
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE xray_records
            SET clinical_description = 'Sin referencia clinica'
            WHERE clinical_description IS NULL OR TRIM(clinical_description) = ''
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE xray_records
            SET image_url = 'pending://missing-image'
            WHERE image_url IS NULL OR TRIM(image_url) = ''
            """
        )
    )

    with op.batch_alter_table("xray_records", schema=None) as batch_op:
        batch_op.alter_column("patient_identifier", existing_type=sa.String(length=50), nullable=False)
        batch_op.alter_column("clinical_description", existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("image_url", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("xray_records", schema=None) as batch_op:
        batch_op.alter_column("image_url", existing_type=sa.String(length=255), nullable=True)
        batch_op.alter_column("clinical_description", existing_type=sa.Text(), nullable=True)
        batch_op.drop_column("patient_identifier")
