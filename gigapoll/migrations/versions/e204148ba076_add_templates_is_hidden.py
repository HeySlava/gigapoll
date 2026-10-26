"""Add templates.is_hidden

Revision ID: e204148ba076
Revises: 6862efa74624
Create Date: 2024-04-18 09:18:19.036756

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e204148ba076'
down_revision: Union[str, None] = '6862efa74624'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('DROP TABLE IF EXISTS _alembic_tmp_polls')
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('is_hidden', sa.Boolean(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.drop_column('is_hidden')
