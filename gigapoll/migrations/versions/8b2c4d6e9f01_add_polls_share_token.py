"""add polls share_token

Revision ID: 8b2c4d6e9f01
Revises: f3a1c9d82e4b
Create Date: 2026-02-06 12:00:00.000000

"""
from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = '8b2c4d6e9f01'
down_revision: Union[str, None] = 'f3a1c9d82e4b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'polls',
        sa.Column('share_token', sa.String(length=32), nullable=True),
    )
    op.create_index(
            'ix_polls_share_token',
            'polls',
            ['share_token'],
            unique=True,
        )


def downgrade() -> None:
    op.drop_index('ix_polls_share_token', table_name='polls')
    with op.batch_alter_table('polls') as batch_op:
        batch_op.drop_column('share_token')
