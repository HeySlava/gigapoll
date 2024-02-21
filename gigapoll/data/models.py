import uuid

from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


meta = MetaData(naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_`%(constraint_name)s`',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s'
      })


class Base(DeclarativeBase):
    metadata = meta


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(
            Integer,
            primary_key=True,
        )

    templates: Mapped[list['Template']] = relationship(back_populates='user')


class Template(Base):
    __tablename__ = 'templates'

    uuid: Mapped[str] = mapped_column(
            String,
            default=lambda: str(uuid.uuid4()).replace('-', ''),
        )
    name: Mapped[str] = mapped_column(
            String,
            primary_key=True,
        )
    user_id: Mapped[int] = mapped_column(
            ForeignKey('users.id'),
            primary_key=True,
        )
    version: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)

    user: Mapped['User'] = relationship(back_populates='templates')

    available_choices = relationship(
            'TemplateChoice',
            back_populates='template',
            cascade='all, delete',
            passive_deletes=True,
        )


class Poll(Base):
    __tablename__ = 'polls'

    message_id: Mapped[int] = mapped_column(
            Integer,
            primary_key=True,
        )
    chat_id: Mapped[int] = mapped_column(Integer)
    message_thread_id: Mapped[int] = mapped_column(Integer, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    template_name: Mapped[str] = mapped_column(String)


class Choice(Base):
    __tablename__ = 'choices'

    id: Mapped[int] = mapped_column(
            Integer,
            primary_key=True,
            autoincrement=True,
        )
    message_id: Mapped[int] = mapped_column(Integer)
    chat_id: Mapped[int] = mapped_column(Integer)
    message_thread_id: Mapped[int] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    choice: Mapped[str] = mapped_column(String)


class TemplateChoice(Base):
    __tablename__ = 'template_choices'

    uuid: Mapped[str] = mapped_column(
            String,
            default=lambda: str(uuid.uuid4()).replace('-', ''),
        )
    template_uuid: Mapped[str] = mapped_column(
            ForeignKey('templates.uuid'),
            primary_key=True,
        )
    name: Mapped[str] = mapped_column(String, primary_key=True)
    is_positive: Mapped[bool] = mapped_column(Boolean, nullable=True)
    is_negative: Mapped[bool] = mapped_column(Boolean, nullable=True)

    template = relationship('Template', back_populates='available_choices')
