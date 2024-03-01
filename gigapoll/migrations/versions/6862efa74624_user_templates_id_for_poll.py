"""User templates.id for poll

Revision ID: 6862efa74624
Revises: 5225756dc365
Create Date: 2024-03-01 16:03:42.943348

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6862efa74624'
down_revision: Union[str, None] = '5225756dc365'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('template_id', sa.Integer(), nullable=False)
        )
        batch_op.drop_constraint('fk_polls_owner_id_users', type_='foreignkey')
        batch_op.create_foreign_key(
            batch_op.f('fk_polls_template_id_templates'),
            'templates',
            ['template_id'],
            ['id'],
        )
        batch_op.drop_column('owner_id')
        batch_op.drop_column('template_name')


def downgrade() -> None:
    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('template_name', sa.VARCHAR(), nullable=False)
        )
        batch_op.add_column(
            sa.Column('owner_id', sa.INTEGER(), nullable=False)
        )
        batch_op.drop_constraint(
            batch_op.f('fk_polls_template_id_templates'), type_='foreignkey'
        )
        batch_op.create_foreign_key(
            'fk_polls_owner_id_users', 'users', ['owner_id'], ['id']
        )
        batch_op.drop_column('template_id')
