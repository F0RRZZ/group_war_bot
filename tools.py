from aiogram.types import Message

from inlines import get_bot_invite_keyboard
from models import User

__all__ = [
    'generate_string_for_top',
    'incline_soldier',
    'get_rank',
    'is_message_in_group',
    'is_message_personal',
    'is_user_can_raid',
]


def generate_string_for_top(users: list[User], is_global=False) -> str:
    if is_global:
        string = '🪖Топ 10 армий в мире:\n'
    else:
        string = '🪖Топ 10 армий в группе:\n'
    for i, user in enumerate(users):
        string += (
            f'{i + 1}. 🎄({get_rank(user.soldiers_count)}) '
            f'{user.first_name} - {user.soldiers_count}'
            f' ({user.wins} побед, {user.defeats} поражений)🎄\n'
        )
    return string


def incline_soldier(number: int) -> str:
    if str(number)[-1] in '10' or number < 20:
        return 'солдат'
    return 'солдата'


def get_rank(soldiers_count: int) -> str:
    ranks = {
        'Рядовой': 50,
        'Ефрейтор': 100,
        'Сержант': 200,
        'Старшина': 300,
        'Лейтенант': 500,
        'Капитан': 1000,
        'Майор': 1500,
        'Полковник': 2000,
        'Генерал': 3000,
    }
    rank = ''
    for key, val in ranks.items():
        if soldiers_count <= val:
            rank = key
            break
    return rank if rank else 'Маршал'


async def is_message_in_group(message: Message) -> bool:
    if message.chat.type not in ('group', 'supergroup'):
        await message.answer(
            '🚫Данная команда доступна только в группах',
            reply_markup=get_bot_invite_keyboard(),
        )
        return False
    return True


async def is_message_personal(message: Message) -> bool:
    if message.chat.type != 'private':
        await message.answer(
            f'🚫@{message.from_user.username}, '
            f'данная команда доступна только в личке с ботом',
        )
        return False
    return True


def is_user_can_raid(
    attacking_user: User,
    defending_user: User,
) -> tuple[bool, str | None]:
    if attacking_user.raided_today:
        return False, 'raided_today'
    if attacking_user.telegram_id == defending_user.telegram_id:
        return False, 'attacked_himself'
    if attacking_user.soldiers_count < 10:
        return False, 'attacking_user_has_fewer_soldiers'
    if defending_user is None:
        return False, 'defending_user_not_found'
    if defending_user.soldiers_count < 10:
        return False, 'defending_user_has_fewer_soldiers'
    return True, None
