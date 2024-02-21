"""Make template_choices wide

Revision ID: 989e2709f6da
Revises: ffdae944f122
Create Date: 2024-02-22 00:04:01.012825

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '989e2709f6da'
down_revision: Union[str, None] = 'ffdae944f122'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('template_choices', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('is_positive', sa.Boolean(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('is_negative', sa.Boolean(), nullable=True)
        )
        batch_op.drop_column('extra')


def downgrade() -> None:
    with op.batch_alter_table('template_choices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('extra', sqlite.JSON(), nullable=True))
        batch_op.drop_column('is_negative')
        batch_op.drop_column('is_positive')
