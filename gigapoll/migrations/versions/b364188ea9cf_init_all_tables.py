"""Init all tables

Revision ID: b364188ea9cf
Revises:
Create Date: 2024-02-23 21:04:27.708987

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b364188ea9cf'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'choices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('message_thread_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('cbdata', sa.String(), nullable=False),
        sa.Column('cdate', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_choices')),
    )
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    )
    op.create_table(
        'polls',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('message_thread_id', sa.Integer(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('template_name', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ['owner_id'], ['users.id'], name=op.f('fk_polls_owner_id_users')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_polls')),
    )
    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_polls_message_id'), ['message_id'], unique=False
        )

    op.create_table(
        'templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('mode', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], name=op.f('fk_templates_user_id_users')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_templates')),
    )
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_templates_name'), ['name'], unique=False
        )

    op.create_table(
        'buttons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('is_positive', sa.Boolean(), nullable=True),
        sa.Column('is_negative', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ['template_id'],
            ['templates.id'],
            name=op.f('fk_buttons_template_id_templates'),
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_buttons')),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('buttons')
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_templates_name'))

    op.drop_table('templates')
    with op.batch_alter_table('polls', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_polls_message_id'))

    op.drop_table('polls')
    op.drop_table('users')
    op.drop_table('choices')
    # ### end Alembic commands ###
