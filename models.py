from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

__all__ = []

DeclarativeBase = declarative_base()

groups_users = sa.Table(
    'groups_users',
    DeclarativeBase.metadata,
    sa.Column('group_id', sa.ForeignKey('groups.id')),
    sa.Column('user_id', sa.ForeignKey('users.id')),
)

promocodes_users = sa.Table(
    'promocodes_users',
    DeclarativeBase.metadata,
    sa.Column('promocode_id', sa.ForeignKey('promocodes.id')),
    sa.Column('user_id', sa.ForeignKey('users.id')),
)


class Group(DeclarativeBase):
    __tablename__ = 'groups'
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    users = orm.relationship(
        'User',
        secondary=groups_users,
        back_populates='groups',
    )
    telegram_id = sa.Column(sa.BigInteger, index=True, unique=True)
    name = sa.Column(sa.String)


class User(DeclarativeBase):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    groups = orm.relationship(
        'Group',
        secondary=groups_users,
        back_populates='users',
    )
    promocodes = orm.relationship(
        'Promocode',
        secondary=promocodes_users,
        back_populates='users',
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


class Promocode(DeclarativeBase):
    __tablename__ = 'promocodes'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    users = orm.relationship(
        'User',
        secondary=promocodes_users,
        back_populates='promocodes',
    )
    name = sa.Column(sa.String)
    bonus_soldiers = sa.Column(sa.Integer)
    is_active = sa.Column(sa.Boolean)


class ParentReferalUser(DeclarativeBase):
    __tablename__ = 'parent_ref_users'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    linked_users = orm.relationship(
        'LinkedReferalUser',
        back_populates='parent_ref_user',
    )
    telegram_id = sa.Column(sa.BigInteger, index=True, unique=True)
    username = sa.Column(sa.String)
    token = sa.Column(sa.String, nullable=False, unique=True)


class LinkedReferalUser(DeclarativeBase):
    __tablename__ = 'linked_ref_users'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    parent_id = sa.Column(sa.Integer, sa.ForeignKey('parent_ref_users.id'))
    parent_ref_user = orm.relationship(
        'ParentReferalUser',
        back_populates='linked_users',
    )
    telegram_id = sa.Column(sa.BigInteger, index=True, unique=True)
    username = sa.Column(sa.String)


class SeasonWinner(DeclarativeBase):
    __tablename__ = 'season_winners'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    telegram_id = sa.Column(sa.BigInteger)
    username = sa.Column(sa.String)
    first_name = sa.Column(sa.String)
    last_name = sa.Column(sa.String)
    soldiers_count = sa.Column(sa.BigInteger, default=0)
    wins = sa.Column(sa.BigInteger, default=0)
    defeats = sa.Column(sa.BigInteger, default=0)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
