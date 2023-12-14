from math import floor
import os
from secrets import token_hex
from random import randint

from aiogram import Router, filters
from aiogram.types import Message
from dotenv import load_dotenv

from inlines import get_bot_invite_keyboard
import queries
import tools
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
        'Также с помощью команды /raid и юзернейма игрока '
        'ты можешь напасть на любого '
        'участника чата, у которого 10 или больше солдат. '
        'С вероятностью 50/50 ты можешь получить 10% от '
        'его армии либо потерять 10% от своей. '
        '(лимит на выигрыш - 20 солдат)\n\n'
        'Если есть вопросы по работе бота, пиши /help',
        reply_markup=keyboard,
    )


@router.message(filters.Command('help'))
async def help(message: Message):
    await message.answer(
        'Команды бота:\n'
        '/army - получить/потерять от -10 до 20 солдат\n'
        '/raid @username - напасть на человека из группы\n'
        '/top_army - топ 10 самых великих армий в группе\n'
        '/global_top - топ 10 самых великих армий в мире\n'
        '/create_token - создать реферальный токен '
        '(с каждой попытки подключенных к вам '
        'пользователей вы будете получать 1 солдата)\n'
        '/my_token - посмотреть свой токен\n'
        '/link - подключиться к другому пользователю и '
        'получить 30 солдат в каждый чат '
        '(вводить можно только 1 раз!)\n\n'
        'Если бот не отвечает на ваши сообщения, попробуйте '
        'ввести команду таким образом: /<команда>@group_war_bot '
        'либо выдайте боту админку\n\n'
        'Наш канал: t.me/group_war'
    )


@router.message(filters.Command('army'))
async def army(message: Message):
    if message.chat.type not in ('group', 'supergroup'):
        await message.answer(
            '🚫Данная команда доступна только в группах',
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
        await message.answer(
            f'🚫@{user.username}, вы уже играли сегодня!\n'
            f'Следующее обновление в 22:00 по МСК'
        )
        return
    rnd_start = -10 if user.soldiers_count >= 10 else -user.soldiers_count
    rnd_start += rnd_start == 0
    delta_army = randint(rnd_start, 20)
    while delta_army == 0:
        delta_army = randint(rnd_start, 20)
    user.soldiers_count += delta_army
    user.increased_today = True
    db_sess.commit()
    word = 'увеличилась' if delta_army > 0 else 'уменьшилась'
    await message.answer(
        f'🪖@{user.username}, ваша армия {word} на '
        f'{abs(delta_army)} {tools.incline_soldier(abs(delta_army))}!\n'
        f'Всего у вас {user.soldiers_count} '
        f'{tools.incline_soldier(user.soldiers_count)}.\n'
        f'Ваше звание: {tools.get_rank(user.soldiers_count)}'
    )
    if queries.is_user_linked(db_sess, message.from_user.id):
        linked_user = queries.get_linked_user(db_sess, message.from_user.id)
        parent_id = linked_user.parent_ref_user.telegram_id
        users = queries.get_all_users_by_id(db_sess, parent_id)
        for user in users:
            user.soldiers_count += 1
        db_sess.commit()


@router.message(filters.Command('raid'))
async def raid(message: Message):
    if message.chat.type not in ('group', 'supergroup'):
        await message.answer(
            '🚫Данная команда доступна только в группах',
            reply_markup=get_bot_invite_keyboard(),
        )
        return
    text = message.text.split()
    if len(text) == 1 or not text[1].startswith('@'):
        await message.answer(
            f'⚠️@{message.from_user.username}, вам нужно '
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
    error_answers = {
        'raided_today': f'🚫@{attacking_user.username}, '
        f'вы уже нападали сегодня!\n'
        f'Следующее обновление в 22:00 по МСК',
        'attacked_himself': f'🚫@{attacking_user.username}, '
        f'нельзя напасть на себя!',
        'attacking_user_has_fewer_soldiers': f'🚫@{attacking_user.username}, '
        f'у вас меньше 10 солдат!',
        'defending_user_not_found': f'🚫@{attacking_user.username}, '
        f'пользователь не найден!',
        'defending_user_has_fewer_soldiers': f'🚫@{attacking_user.username}, '
        f'у пользователя меньше 10 солдат!',
    }
    is_user_can_raid = tools.is_user_can_raid(attacking_user, defending_user)
    if not is_user_can_raid[0]:
        await message.answer(error_answers[is_user_can_raid[1]])
        return
    result = randint(0, 1)
    if result:
        if floor(defending_user.soldiers_count / 10) > 20:
            attacking_user.soldiers_count += 20
            delta = 20
        else:
            attacking_user.soldiers_count += floor(
                defending_user.soldiers_count / 10
            )
            delta = int(floor(defending_user.soldiers_count / 10))
        soldiers_delta = attacking_user.soldiers_count
        await message.answer(
            f'🪖@{attacking_user.username} в результате боя вы получили '
            f'{delta} {tools.incline_soldier(delta)}.\n'
            f'Всего у вас {soldiers_delta} '
            f'{tools.incline_soldier(soldiers_delta)}\n'
            f'Ваше звание: {tools.get_rank(soldiers_delta)}'
        )
        defending_user.soldiers_count -= delta
        attacking_user.wins += 1
        defending_user.defeats += 1
    else:
        if floor(attacking_user.soldiers_count / 10) > 20:
            defending_user.soldiers_count += 20
            delta = 20
        else:
            defending_user.soldiers_count += floor(
                attacking_user.soldiers_count / 10
            )
            delta = int(floor(attacking_user.soldiers_count / 10))
        soldiers_delta = attacking_user.soldiers_count - delta
        await message.answer(
            f'🪖@{attacking_user.username} в результате боя вы потеряли '
            f'{delta} {tools.incline_soldier(delta)}.'
            f'Всего у вас {soldiers_delta} '
            f'{tools.incline_soldier(soldiers_delta)}\n'
            f'Ваше звание: {tools.get_rank(soldiers_delta)}'
        )
        attacking_user.soldiers_count -= delta
        attacking_user.defeats += 1
        defending_user.wins += 1
    attacking_user.raided_today = True
    db_sess.commit()


@router.message(filters.Command('top_army'))
async def top_army(message: Message):
    if message.chat.type not in ('group', 'supergroup'):
        await message.answer(
            '🚫Данная команда доступна только в группах',
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
    await message.answer(tools.generate_string_for_top(users, is_global=False))


@router.message(filters.Command('global_top'))
async def global_top(message: Message):
    db_sess = db_session.create_session()
    users = queries.get_users_for_global_top(db_sess)
    await message.answer(tools.generate_string_for_top(users, is_global=True))


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
            f'🚫Промокода {promocode} не существует, либо он неактивен.'
        )
        return
    if queries.is_user_used_promo(db_sess, message, promocode):
        await message.answer('🚫Вы уже использовали данный промокод!')
        return
    promocode = queries.get_promocode_by_name(db_sess, promocode)
    users = queries.get_all_users_by_id(db_sess, message.from_user.id)
    if not users:
        await message.answer('🚫Вас нет ни в одной группе с ботом!')
        return
    queries.add_user_to_promocode_list(db_sess, message, promocode)
    for user in users:
        user.soldiers_count += promocode.bonus_soldiers
    db_sess.commit()
    await message.answer(
        f'✅Вы получили бонус в размере {promocode.bonus_soldiers} '
        f'{tools.incline_soldier(promocode.bonus_soldiers)}'
    )


@router.message(filters.Command('create_token'))
async def create_token(message: Message):
    if message.chat.type != 'private':
        await message.answer(
            f'🚫@{message.from_user.username}, '
            f'данная команда доступна только в личке с ботом'
        )
        return
    db_sess = db_session.create_session()
    if queries.is_user_parent_ref(db_sess, message):
        ref = queries.get_parent_ref_by_id(db_sess, message)
        await message.answer(
            f'⚠️У вас уже есть реферальный токен: `{ref.token}`',
            parse_mode='MARKDOWN',
        )
        return
    token = token_hex(16)
    queries.create_parent_ref(db_sess, message, token)
    await message.answer(
        f'🌐Ваш реферальный токен: `{token}`\n\n '
        f'Теперь вы можете передавать его своим '
        f'друзьям и получать 1 солдата в каждый чат с каждой их попытки',
        parse_mode='MARKDOWN',
    )


@router.message(filters.Command('my_token'))
async def my_token(message: Message):
    if message.chat.type != 'private':
        await message.answer(
            f'🚫@{message.from_user.username}, '
            f'данная команда доступна только в личке с ботом'
        )
        return
    db_sess = db_session.create_session()
    if not queries.is_user_parent_ref(db_sess, message):
        await message.answer(
            '⚠️Вы еще не создали токен. Чтобы создать введите /create_token'
        )
        return
    ref = queries.get_parent_ref_by_id(db_sess, message)
    await message.answer(
        f'🌐Ваш токен: `{ref.token}`',
        parse_mode='MARKDOWN',
    )


@router.message(filters.Command('link'))
async def link(message: Message):
    if message.chat.type != 'private':
        await message.answer(
            f'🚫@{message.from_user.username}, '
            f'данная команда доступна только в личке с ботом'
        )
        return
    if len(message.text.split()) == 1:
        await message.answer('🚫Введите токен')
        return
    token = message.text.split()[1]
    db_sess = db_session.create_session()
    if queries.is_user_linked(db_sess, message.chat.id):
        linked_user = queries.get_linked_user(db_sess, message.chat.id)
        await message.answer(
            f'🚫Вы уже привязаны к пользователю '
            f'@{linked_user.parent_ref_user.username}'
        )
        return
    parent_user = queries.get_parent_ref_by_token(db_sess, token)
    if not parent_user:
        await message.answer('🚫Такого токена не существует')
        return
    if parent_user.telegram_id == message.chat.id:
        await message.answer('🚫Нельзя подключиться к себе же')
        return
    queries.create_linked_user(db_sess, message, parent_user)
    users = queries.get_all_users_by_id(db_sess, message.chat.id)
    for user in users:
        user.soldiers_count += 30
    db_sess.commit()
    await message.answer(
        f'✅Вы привязаны к пользователю @{parent_user.username}\n\n'
        f'Также вам начисленно 30 солдат во все чаты'
    )
