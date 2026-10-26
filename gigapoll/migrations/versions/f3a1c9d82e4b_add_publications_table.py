"""Add publications table

Revision ID: f3a1c9d82e4b
Revises: e204148ba076
Create Date: 2026-03-12 00:00:00.000000

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f3a1c9d82e4b'
down_revision: Union[str, None] = 'e204148ba076'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'publications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('poll_id', sa.Integer(), nullable=False),
        sa.Column('inline_message_id', sa.String(), nullable=False),
        sa.Column('cdate', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['poll_id'], ['polls.id'],
            name='fk_publications_poll_id_polls',
        ),
        sa.PrimaryKeyConstraint('id', name='pk_publications'),
        sa.UniqueConstraint(
            'inline_message_id',
            name='uq_publications_inline_message_id',
        ),
    )


def downgrade() -> None:
    op.drop_table('publications')
