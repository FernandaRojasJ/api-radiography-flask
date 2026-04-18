"""update_xray_records_constraints

Revision ID: b5112f27c258
Revises: 
Create Date: 2026-04-15 18:41:26.704230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b5112f27c258'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('xray_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('patient_full_name', sa.String(length=100), nullable=False),
    sa.Column('clinical_history_code', sa.String(length=50), nullable=False),
    sa.Column('clinical_description', sa.Text(), nullable=True),
    sa.Column('study_date', sa.DateTime(), nullable=False),
    sa.Column('image_url', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('clinical_history_code')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('xray_records')
