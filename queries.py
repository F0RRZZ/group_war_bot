from aiogram.types import Message
from sqlalchemy import func
from sqlalchemy.orm import Session

import models

__all__ = []


def create_group(db_sess: Session, message: Message) -> None:
    new_group = models.Group(
        telegram_id=message.chat.id,
        name=message.chat.title,
    )
    db_sess.add(new_group)
    db_sess.commit()


def create_user(db_sess: Session, message: Message) -> None:
    group = get_group_by_telegram_id(db_sess, message.chat.id)
    new_user = models.User(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    db_sess.add(new_user)
    group.users.append(new_user)
    db_sess.commit()


def is_promocode_exists_and_active(db_sess: Session, promocode: str) -> bool:
    promocode = get_promocode_by_name(db_sess, promocode)
    if not promocode:
        return False
    return promocode.is_active


def is_user_used_promo(
    db_sess: Session, message: Message, promocode: str
) -> bool:
    promocode = get_promocode_by_name(db_sess, promocode)
    for user in promocode.users:
        if user.telegram_id == message.from_user.id:
            return True
    return False


def add_user_to_promocode_list(
    db_sess: Session, message: Message, promocode: models.Promocode
) -> None:
    user = get_user_id_by_username(db_sess, message.from_user.username)
    user = (
        db_sess.query(models.User)
        .filter(models.User.telegram_id == user)
        .first()
    )
    promocode.users.append(user)
    db_sess.commit()


def get_group_by_telegram_id(
    db_sess: Session, telegram_id: int
) -> models.Group:
    return (
        db_sess.query(models.Group)
        .filter(models.Group.telegram_id == telegram_id)
        .first()
    )


def get_user_id_by_username(db_sess: Session, username: str) -> int | None:
    user = (
        db_sess.query(models.User)
        .filter(models.User.username == username)
        .first()
    )
    if user:
        return user.telegram_id
    return None


def get_promocode_by_name(
    db_sess: Session, promocode: str
) -> models.Promocode:
    return (
        db_sess.query(models.Promocode)
        .filter(models.Promocode.name == promocode)
        .first()
    )


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


def get_user_from_group(
    db_sess: Session, chat_id: int, user_id: int
) -> models.User:
    group = get_group_by_telegram_id(db_sess, chat_id)
    from_user = None
    for user in group.users:
        if user.telegram_id == user_id:
            from_user = user
            break
    return from_user


def get_users_for_global_top(db_sess: Session) -> list[models.User]:
    return (
        db_sess.query(models.User)
        .order_by(models.User.soldiers_count.desc())
        .limit(10)
        .all()
    )


def get_all_users_by_id(
    db_sess: Session, telegram_id: int
) -> list[models.User]:
    return (
        db_sess.query(models.User)
        .filter(models.User.telegram_id == telegram_id)
        .all()
    )


def change_username(db_sess: Session, message: Message) -> None:
    users = get_all_users_by_id(db_sess, message.from_user.id)
    for user in users:
        user.username = message.from_user.username
    db_sess.commit()


def add_new_user_and_group_and_change_username(
    db_sess: Session, message: Message
) -> None:
    add_new_user_and_group_in_db(db_sess, message)
    change_username(db_sess, message)


def is_user_parent_ref(db_sess: Session, message: Message) -> bool:
    parents = (
        db_sess.query(models.ParentReferalUser)
        .filter(models.ParentReferalUser.telegram_id == message.chat.id)
        .first()
    )
    return bool(parents)


def create_parent_ref(db_sess: Session, message: Message, token: str) -> None:
    new_ref = models.ParentReferalUser(
        telegram_id=message.chat.id,
        username=message.chat.username,
        token=token,
    )
    db_sess.add(new_ref)
    db_sess.commit()


def get_parent_ref_by_id(
    db_sess: Session, message: Message
) -> models.ParentReferalUser:
    return (
        db_sess.query(models.ParentReferalUser)
        .filter(models.ParentReferalUser.telegram_id == message.chat.id)
        .first()
    )


def get_parent_ref_by_token(
    db_sess: Session, token: str
) -> models.ParentReferalUser:
    return (
        db_sess.query(models.ParentReferalUser)
        .filter(models.ParentReferalUser.token == token)
        .first()
    )


def is_user_linked(db_sess: Session, telegram_id: int) -> bool:
    linked_user = (
        db_sess.query(models.LinkedReferalUser)
        .filter(models.LinkedReferalUser.telegram_id == telegram_id)
        .first()
    )
    return bool(linked_user)


def create_linked_user(
    db_sess: Session, message: Message, parent: models.ParentReferalUser
) -> None:
    linked_user = models.LinkedReferalUser(
        parent_ref_user=parent,
        telegram_id=message.chat.id,
        username=message.chat.username,
    )
    db_sess.add(linked_user)
    db_sess.commit()


def get_linked_user(
    db_sess: Session, telegram_id: int
) -> models.LinkedReferalUser:
    return (
        db_sess.query(models.LinkedReferalUser)
        .filter(models.LinkedReferalUser.telegram_id == telegram_id)
        .first()
    )
