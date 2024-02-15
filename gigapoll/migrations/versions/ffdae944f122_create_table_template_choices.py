"""Create table template_choices

Revision ID: ffdae944f122
Revises: d36e447d2185
Create Date: 2024-02-15 18:19:33.341973

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'ffdae944f122'
down_revision: Union[str, None] = 'd36e447d2185'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'template_choices',
        sa.Column('template_name', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('extra', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ['template_name'],
            ['templates.name'],
            name=op.f('fk_template_choices_template_name_templates'),
        ),
        sa.PrimaryKeyConstraint(
            'template_name', 'name', name=op.f('pk_template_choices')
        ),
    )
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.drop_column('choices')


def downgrade() -> None:
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('choices', sqlite.JSON(), nullable=True)
        )

    op.drop_table('template_choices')
