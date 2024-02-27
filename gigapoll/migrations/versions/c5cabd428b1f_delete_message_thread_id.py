"""Delete message_thread_id

Revision ID: c5cabd428b1f
Revises: fc80f1f71330
Create Date: 2024-02-28 00:56:07.425365

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c5cabd428b1f'
down_revision: Union[str, None] = 'fc80f1f71330'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('choices', schema=None) as batch_op:
        batch_op.drop_column('message_thread_id')

    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.drop_column('message_thread_id')


def downgrade() -> None:
    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('message_thread_id', sa.INTEGER(), nullable=True)
        )

    with op.batch_alter_table('choices', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('message_thread_id', sa.INTEGER(), nullable=True)
        )
