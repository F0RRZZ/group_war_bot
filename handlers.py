from math import floor
import os
from random import randint

from aiogram import Router, filters
from aiogram.types import Message
from dotenv import load_dotenv

from inlines import get_bot_invite_keyboard
import queries
from tools import generate_string_for_top
from utils import db_session

__all__ = []

load_dotenv()

router = Router()

db_session.global_init(
    user=os.getenv('DB_USER'),
    port=os.getenv('DB_PORT'),
    host=os.getenv('DB_HOST'),
    db_name=os.getenv('DB_NAME'),
    password=os.getenv('DB_PASSWORD'),
)


@router.message(filters.Command('start'))
async def start(message: Message):
    keyboard = get_bot_invite_keyboard()
    await message.answer(
        'Привет! Я Group War Bot\n\nВ чем смысл бота?\n'
        'Каждые 24 часа ты можешь ввести команду /army, '
        'где можешь получить случайное количество '
        'солдат от -10 до 20 солдат.\n'
        'Также с помощью команды /rade и юзернейма игрока '
        'ты можешь напасть на любого '
        'участника чата, у которого 10 или больше солдат. '
        'С вероятностью 50/50 ты можешь получить 10% от '
        'его армии либо потерять 10% от своей.\n\n'
        'Если есть вопросы по работе бота, пиши /help',
        reply_markup=keyboard,
    )


@router.message(filters.Command('help'))
async def help(message: Message):
    await message.answer(
        'Команды бота:\n'
        '/army - получить/потерять от -10 до 20 солдат\n'
        '/rade @username - напасть на человека из группы\n'
        '/top_army - топ 10 самых великих армий в группе\n'
        '/global_top - топ 10 самых великих армий в мире\n\n'
        'Наш канал: t.me/group_war'
    )


@router.message(filters.Command('army'))
async def army(message: Message):
    if message.chat.type not in ('group', 'supergroup'):
        await message.answer(
            'Данная команда доступна только в группах',
            reply_markup=get_bot_invite_keyboard(),
        )
        return
    db_sess = db_session.create_session()
    queries.add_new_user_and_group_in_db(db_sess, message)
    queries.change_username(db_sess, message)
    user = queries.get_user_from_group(
        db_sess, message.chat.id, message.from_user.id
    )
    if user.increased_today:
        await message.answer(f'@{user.username}, вы уже играли сегодня!')
        return
    rnd_start = -10 if user.soldiers_count >= 10 else -user.soldiers_count
    delta_army = (
        randint(1, 20) if user.soldiers_count == 0 else randint(rnd_start, 20)
    )
    while delta_army == 0:
        delta_army = randint(-10, 20)
    user.soldiers_count += delta_army
    user.increased_today = True
    db_sess.commit()
    word = 'увеличилась' if delta_army > 0 else 'уменьшилась'
    await message.answer(
        f'@{user.username}, ваша армия {word} на {abs(delta_army)} солдата!\n'
        f'Всего у вас {user.soldiers_count} солдата.'
    )


@router.message(filters.Command('raid'))
async def raid(message: Message):
    if message.chat.type not in ('group', 'supergroup'):
        await message.answer(
            'Данная команда доступна только в группах',
            reply_markup=get_bot_invite_keyboard(),
        )
        return
    text = message.text.split()
    if len(text) == 1 or not text[1].startswith('@'):
        await message.answer(
            f'@{message.from_user.username}, вам нужно '
            f'отметить участника группы',
        )
        return
    username = text[1][1:]
    db_sess = db_session.create_session()
    queries.add_new_user_and_group_in_db(db_sess, message)
    queries.change_username(db_sess, message)
    attacking_user = queries.get_user_from_group(
        db_sess, message.chat.id, message.from_user.id
    )
    defending_user = queries.get_user_id_by_username(db_sess, username)
    defending_user = queries.get_user_from_group(
        db_sess, message.chat.id, defending_user
    )
    if attacking_user.raided_today:
        await message.answer(
            f'@{attacking_user.username}, вы уже нападали сегодня!',
        )
        return
    if attacking_user.telegram_id == defending_user.telegram_id:
        await message.answer(
            f'@{attacking_user.username}, нельзя напасть на себя!',
        )
        return
    if attacking_user.soldiers_count < 10:
        await message.answer(
            f'@{attacking_user.username}, у вас меньше 10 солдат!',
        )
        return
    if defending_user is None:
        await message.answer(
            f'@{attacking_user.username}, пользователь не найден!',
        )
        return
    if defending_user.soldiers_count < 10:
        await message.answer(
            f'@{attacking_user.username}, у пользователя меньше 10 солдат!',
        )
    result = randint(0, 1)
    if result:
        attacking_user.soldiers_count += floor(
            defending_user.soldiers_count / 10
        )
        await message.answer(
            f'@{attacking_user.username} в результате боя вы получили '
            f'{int(floor(defending_user.soldiers_count / 10))} солдат.'
        )
        defending_user.soldiers_count -= floor(
            defending_user.soldiers_count / 10
        )
        attacking_user.wins += 1
        defending_user.defeats += 1
    else:
        defending_user.soldiers_count += floor(
            attacking_user.soldiers_count / 10
        )
        await message.answer(
            f'@{attacking_user.username} в результате боя вы потеряли '
            f'{int(floor(attacking_user.soldiers_count / 10))} солдат.'
        )
        attacking_user.soldiers_count -= floor(
            attacking_user.soldiers_count / 10
        )
        attacking_user.defeats += 1
        defending_user.wins += 1
    attacking_user.raided_today = True
    db_sess.commit()


@router.message(filters.Command('top_army'))
async def top_army(message: Message):
    if message.chat.type not in ('group', 'supergroup'):
        await message.answer(
            'Данная команда доступна только в группах',
            reply_markup=get_bot_invite_keyboard(),
        )
        return
    db_sess = db_session.create_session()
    group = queries.get_group_by_telegram_id(db_sess, message.chat.id)
    users = sorted(
        group.users,
        key=lambda user: user.soldiers_count,
        reverse=True,
    )[:10]
    await message.answer(generate_string_for_top(users, is_global=False))


@router.message(filters.Command('global_top'))
async def global_top(message: Message):
    db_sess = db_session.create_session()
    users = queries.get_users_for_global_top(db_sess)
    await message.answer(generate_string_for_top(users, is_global=True))


@router.message(filters.Command('promo'))
async def promo(message: Message):
    if message.chat.type != 'private':
        await message.answer(
            f'🚫@{message.from_user.username}, '
            f'данная команда доступна только в личке с ботом'
        )
        return
    if len(message.text.split()) == 1:
        await message.answer('🚫Введите промокод')
        return
    db_sess = db_session.create_session()
    promocode = message.text.split()[1]
    if not queries.is_promocode_exists_and_active(db_sess, promocode):
        await message.answer(
            f'Промокода {promocode} не существует, либо он неактивен.'
        )
        return
    if queries.is_user_used_promo(db_sess, message, promocode):
        await message.answer('Вы уже использовали данный промокод!')
        return
    promocode = queries.get_promocode_by_name(db_sess, promocode)
    users = queries.get_all_users_by_id(db_sess, message)
    if not users:
        await message.answer('Вас нет ни в одной группе с ботом!')
        return
    queries.add_user_to_promocode_list(db_sess, message, promocode)
    for user in users:
        user.soldiers_count += promocode.bonus_soldiers
    db_sess.commit()
    await message.answer(
        f'✅Вы получили бонус в размере {promocode.bonus_soldiers} солдат'
    )
