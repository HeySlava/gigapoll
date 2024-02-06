"""choices autoincrement pk

Revision ID: e1a0283d0158
Revises: ce7c03e87450
Create Date: 2024-02-06 22:32:33.880838

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e1a0283d0158'
down_revision: Union[str, None] = 'ce7c03e87450'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'choices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('message_thread_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('choice', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_choices')),
    )


def downgrade() -> None:
    op.drop_table('choices')
