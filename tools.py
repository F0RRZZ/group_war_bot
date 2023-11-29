from aiogram.types import Message
from sqlalchemy.orm import Session

from models import User


def generate_string_for_top(users: list[User], is_global=False) -> str:
    if is_global:
        string = '🪖Топ 10 армий в группе:\n'
    else:
        string = '🪖Топ 10 армий в мире:\n'
    for i, user in enumerate(users):
        string += (
            f'{i + 1}. {user.first_name} - {user.soldiers_count}'
            f'({user.wins} побед, {user.defeats} поражений)\n'
        )
    return string
