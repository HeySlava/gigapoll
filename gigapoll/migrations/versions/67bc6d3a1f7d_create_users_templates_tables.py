"""Create users, templates tables

Revision ID: 67bc6d3a1f7d
Revises:
Create Date: 2024-02-03 11:19:24.316817

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '67bc6d3a1f7d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    )
    op.create_table(
        'templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], name=op.f('fk_templates_user_id_users')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_templates')),
    )


def downgrade() -> None:
    op.drop_table('templates')
    op.drop_table('users')
