"""Add FK to buttons.cbdata

Revision ID: fc80f1f71330
Revises: b364188ea9cf
Create Date: 2024-02-23 22:25:16.011618

"""
from typing import Sequence
from typing import Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'fc80f1f71330'
down_revision: Union[str, None] = 'b364188ea9cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('choices', schema=None) as batch_op:
        batch_op.create_foreign_key(
            batch_op.f('fk_choices_cbdata_buttons'),
            'buttons',
            ['cbdata'],
            ['id'],
        )


def downgrade() -> None:
    with op.batch_alter_table('choices', schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f('fk_choices_cbdata_buttons'), type_='foreignkey'
        )
