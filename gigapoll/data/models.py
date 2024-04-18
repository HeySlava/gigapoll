import datetime as dt

from sqlalchemy import Boolean
from sqlalchemy import DateTime
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

    id: Mapped[int] = mapped_column(
            Integer,
            autoincrement=True,
            primary_key=True,
        )
    name: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    version: Mapped[int] = mapped_column(Integer, default=1)
    mode: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=True)

    user: Mapped['User'] = relationship(back_populates='templates')
    available_choices = relationship(
            'Button',
            back_populates='template',
            cascade='all, delete',
            passive_deletes=True,
        )


class Poll(Base):
    __tablename__ = 'polls'

    id: Mapped[int] = mapped_column(
            Integer,
            autoincrement=True,
            primary_key=True,
        )
    template_id: Mapped[int] = mapped_column(ForeignKey('templates.id'))


class Choice(Base):
    __tablename__ = 'choices'

    id: Mapped[int] = mapped_column(
            Integer,
            primary_key=True,
            autoincrement=True,
        )
    user_id: Mapped[int] = mapped_column(Integer)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    button_id: Mapped[int] = mapped_column(
            Integer,
            ForeignKey('buttons.id'),
        )
    poll_id: Mapped[int] = mapped_column(
            Integer,
            ForeignKey('polls.id'),
        )
    cdate: Mapped[dt.datetime] = mapped_column(
            DateTime,
            default=dt.datetime.utcnow,
        )


class Button(Base):
    __tablename__ = 'buttons'

    id: Mapped[int] = mapped_column(
            Integer,
            primary_key=True,
            autoincrement=True,
        )
    template_id: Mapped[str] = mapped_column(
            ForeignKey('templates.id'),
        )
    value: Mapped[str] = mapped_column(String)
    is_positive: Mapped[bool] = mapped_column(Boolean, nullable=True)
    is_negative: Mapped[bool] = mapped_column(Boolean, nullable=True)

    template = relationship('Template', back_populates='available_choices')
