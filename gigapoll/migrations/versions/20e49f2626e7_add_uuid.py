"""Add uuid

Revision ID: 20e49f2626e7
Revises: b805cd9906c1
Create Date: 2024-02-22 01:59:58.575737

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '20e49f2626e7'
down_revision: Union[str, None] = 'b805cd9906c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('template_choices', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('template_uuid', sa.String(), nullable=False)
        )
        batch_op.drop_constraint(
            'fk_template_choices_template_name_templates', type_='foreignkey'
        )
        batch_op.create_foreign_key(
            batch_op.f('fk_template_choices_template_uuid_templates'),
            'templates',
            ['template_uuid'],
            ['uuid'],
        )
        batch_op.drop_column('template_name')

    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uuid', sa.String(), nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.drop_column('uuid')

    with op.batch_alter_table('template_choices', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('template_name', sa.VARCHAR(), nullable=False)
        )
        batch_op.drop_constraint(
            batch_op.f('fk_template_choices_template_uuid_templates'),
            type_='foreignkey',
        )
        batch_op.create_foreign_key(
            'fk_template_choices_template_name_templates',
            'templates',
            ['template_name'],
            ['name'],
        )
        batch_op.drop_column('template_uuid')
