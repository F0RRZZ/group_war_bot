from aiogram.types import Message
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Group, User

__all__ = []


def create_group(db_sess: Session, message: Message) -> None:
    new_group = Group(
        telegram_id=message.chat.id,
        name=message.chat.title,
    )
    db_sess.add(new_group)
    db_sess.commit()


def create_user(db_sess: Session, message: Message) -> None:
    group = get_group_by_telegram_id(db_sess, message.chat.id)
    new_user = User(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    db_sess.add(new_user)
    group.users.append(new_user)
    db_sess.commit()


def get_group_by_telegram_id(db_sess: Session, telegram_id: int) -> Group:
    return (
        db_sess.query(Group).filter(Group.telegram_id == telegram_id).first()
    )


def get_user_id_by_username(db_sess: Session, username: str) -> int | None:
    user = db_sess.query(User).filter(User.username == username).first()
    if user:
        return user.telegram_id
    return None


def is_group_exists(db_sess: Session, message: Message) -> bool:
    return bool(get_group_by_telegram_id(db_sess, message.chat.id))


def is_user_exists(db_sess: Session, message: Message) -> bool:
    group = get_group_by_telegram_id(db_sess, message.chat.id)
    return message.from_user.id in [user.telegram_id for user in group.users]


def add_new_user_and_group_in_db(db_sess: Session, message: Message) -> None:
    if not is_group_exists(db_sess, message):
        create_group(db_sess, message)
    if not is_user_exists(db_sess, message):
        create_user(db_sess, message)


def get_user_from_group(db_sess: Session, chat_id: int, user_id: int) -> User:
    group = get_group_by_telegram_id(db_sess, chat_id)
    from_user = None
    for user in group.users:
        if user.telegram_id == user_id:
            from_user = user
            break
    return from_user


def get_users_for_global_top(db_sess: Session) -> list[User]:
    return (
        db_sess.query(User)
        .order_by(User.soldiers_count.desc())
        .limit(10)
        .all()
    )
