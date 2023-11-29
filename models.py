import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

DeclarativeBase = declarative_base()

groups_users = sa.Table(
    'groups_users',
    DeclarativeBase.metadata,
    sa.Column('group_id', sa.ForeignKey('groups.id')),
    sa.Column('user_id', sa.ForeignKey('users.id')),
)


class Group(DeclarativeBase):
    __tablename__ = 'groups'
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    users = orm.relationship(
        'User', secondary=groups_users, back_populates='groups'
    )
    telegram_id = sa.Column(sa.BigInteger, index=True, unique=True)
    name = sa.Column(sa.String)


class User(DeclarativeBase):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    groups = orm.relationship(
        'Group', secondary=groups_users, back_populates='users'
    )
    telegram_id = sa.Column(sa.BigInteger)
    username = sa.Column(sa.String)
    first_name = sa.Column(sa.String)
    last_name = sa.Column(sa.String)
    soldiers_count = sa.Column(sa.BigInteger, default=0)
    wins = sa.Column(sa.BigInteger, default=0)
    defeats = sa.Column(sa.BigInteger, default=0)
    increased_today = sa.Column(sa.Boolean, default=False)
    raided_today = sa.Column(sa.Boolean, default=False)
