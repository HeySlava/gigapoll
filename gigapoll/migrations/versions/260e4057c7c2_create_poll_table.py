"""Create poll table

Revision ID: 260e4057c7c2
Revises: 62e6380ca552
Create Date: 2024-02-03 18:36:06.536110

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '260e4057c7c2'
down_revision: Union[str, None] = '62e6380ca552'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'polls',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('message_thread_id', sa.Integer(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('config', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ['owner_id'], ['users.id'], name=op.f('fk_polls_owner_id_users')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_polls')),
    )


def downgrade() -> None:
    op.drop_table('polls')
