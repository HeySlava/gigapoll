"""Get away from chat_id and message_id

Revision ID: 5225756dc365
Revises: c5cabd428b1f
Create Date: 2024-02-28 01:01:17.256807

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5225756dc365'
down_revision: Union[str, None] = 'c5cabd428b1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('choices', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('button_id', sa.Integer(), nullable=False)
        )
        batch_op.add_column(sa.Column('poll_id', sa.Integer(), nullable=False))
        batch_op.drop_constraint(
            'fk_choices_cbdata_buttons', type_='foreignkey'
        )
        batch_op.create_foreign_key(
            batch_op.f('fk_choices_poll_id_polls'),
            'polls',
            ['poll_id'],
            ['id'],
        )
        batch_op.create_foreign_key(
            batch_op.f('fk_choices_button_id_buttons'),
            'buttons',
            ['button_id'],
            ['id'],
        )
        batch_op.drop_column('chat_id')
        batch_op.drop_column('message_id')
        batch_op.drop_column('cbdata')

    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.drop_index('ix_polls_message_id')
        batch_op.drop_column('chat_id')
        batch_op.drop_column('message_id')


def downgrade() -> None:
    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('message_id', sa.INTEGER(), nullable=False)
        )
        batch_op.add_column(sa.Column('chat_id', sa.INTEGER(), nullable=False))
        batch_op.create_index(
            'ix_polls_message_id', ['message_id'], unique=False
        )

    with op.batch_alter_table('choices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cbdata', sa.VARCHAR(), nullable=False))
        batch_op.add_column(
            sa.Column('message_id', sa.INTEGER(), nullable=False)
        )
        batch_op.add_column(sa.Column('chat_id', sa.INTEGER(), nullable=False))
        batch_op.drop_constraint(
            batch_op.f('fk_choices_button_id_buttons'), type_='foreignkey'
        )
        batch_op.drop_constraint(
            batch_op.f('fk_choices_poll_id_polls'), type_='foreignkey'
        )
        batch_op.create_foreign_key(
            'fk_choices_cbdata_buttons', 'buttons', ['cbdata'], ['id']
        )
        batch_op.drop_column('poll_id')
        batch_op.drop_column('button_id')
