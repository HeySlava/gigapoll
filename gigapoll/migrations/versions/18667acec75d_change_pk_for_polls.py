"""Change pk for polls

Revision ID: 18667acec75d
Revises: 260e4057c7c2
Create Date: 2024-02-06 20:55:43.407465

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '18667acec75d'
down_revision: Union[str, None] = '260e4057c7c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('message_id', sa.Integer(), nullable=False)
        )
        batch_op.drop_column('id')


def downgrade() -> None:
    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id', sa.INTEGER(), nullable=False))
        batch_op.drop_column('message_id')
