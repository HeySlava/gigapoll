"""Extend template table

Revision ID: 7fc1f37605d7
Revises: e1a0283d0158
Create Date: 2024-02-10 20:18:58.594677

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7fc1f37605d7'
down_revision: Union[str, None] = 'e1a0283d0158'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('mode', sa.String(), nullable=False))
        batch_op.add_column(
            sa.Column('description', sa.String(), nullable=False)
        )
        batch_op.add_column(sa.Column('choices', sa.JSON(), nullable=False))
        batch_op.drop_column('content')


def downgrade() -> None:
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('content', sa.VARCHAR(), nullable=False))
        batch_op.drop_column('choices')
        batch_op.drop_column('description')
        batch_op.drop_column('mode')
        batch_op.drop_column('version')
