"""Add choice_template.uuid

Revision ID: b805cd9906c1
Revises: 989e2709f6da
Create Date: 2024-02-22 01:46:54.184701

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b805cd9906c1'
down_revision: Union[str, None] = '989e2709f6da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('template_choices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uuid', sa.String(), nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('template_choices', schema=None) as batch_op:
        batch_op.drop_column('uuid')
