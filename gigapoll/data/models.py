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

    name: Mapped[str] = mapped_column(
            String,
            primary_key=True,
        )
    content: Mapped[str] = mapped_column(String)
    user_id: Mapped[int] = mapped_column(
            ForeignKey('users.id'),
            primary_key=True,
        )

    user: Mapped['User'] = relationship(back_populates='templates')

    # from sqlalchemy import UniqueConstraint
    # __table_args__ = (
    #     UniqueConstraint('name', 'room_id'),
    # )


class Poll(Base):
    __tablename__ = 'polls'

    message_id: Mapped[int] = mapped_column(
            Integer,
            primary_key=True,
        )
    chat_id: Mapped[int] = mapped_column(Integer)
    message_thread_id: Mapped[int] = mapped_column(Integer, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    config: Mapped[str] = mapped_column(String)


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
