from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

__all__ = ['get_confirm_button_keyboard']


def get_confirm_button_keyboard() -> InlineKeyboardMarkup:
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text='Добавить', callback_data='add_button')
    keyboard_builder.button(text='Не добавлять', callback_data='no_button')
    keyboard_builder.adjust(1)
    return keyboard_builder.as_markup()


def get_bot_invite_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text='Добавь меня в группу',
        url='https://t.me/group_war_bot?startgroup=Lichka',
    )
    keyboard.adjust(1)
    return keyboard.as_markup()
