"""Create a choices table

Revision ID: fb7ccad21eb5
Revises: 18667acec75d
Create Date: 2024-02-06 21:35:19.689244

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'fb7ccad21eb5'
down_revision: Union[str, None] = '18667acec75d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'choices',
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('message_thread_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('choice', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('message_id', name=op.f('pk_choices')),
    )


def downgrade() -> None:
    op.drop_table('choices')
