"""choices autoincrement pk

Revision ID: 2414952de7e3
Revises: fb7ccad21eb5
Create Date: 2024-02-06 22:24:51.843647

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '2414952de7e3'
down_revision: Union[str, None] = 'fb7ccad21eb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('choices', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False)
        )


def downgrade() -> None:
    with op.batch_alter_table('choices', schema=None) as batch_op:
        batch_op.drop_column('id')
