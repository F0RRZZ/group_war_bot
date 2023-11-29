import os

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from inlines import get_confirm_button_keyboard
from models import Group
from states import BroadcastStatesGroup
from utils import db_session

__all__ = [
    'broadcast',
    'get_confirm_button_keyboard',
    'get_text_button',
    'get_broadcast_message',
    'get_button_url',
    'add_button',
    'confirm',
    'broadcast_confirmation',
]

load_dotenv()

db_session.global_init(
    user=os.getenv('DB_USER'),
    port=os.getenv('DB_PORT'),
    host=os.getenv('DB_HOST'),
    db_name=os.getenv('DB_NAME'),
    password=os.getenv('DB_PASSWORD'),
)


async def broadcast(message: Message, state: FSMContext):
    if message.chat.id != int(os.getenv('ADMIN_ID')):
        return
    await message.answer('Отправьте рекламное сообщение')
    await state.set_state(BroadcastStatesGroup.get_message)


async def get_broadcast_message(message: Message, state: FSMContext):
    await message.answer(
        'Хотите добавить кнопку?',
        reply_markup=get_confirm_button_keyboard(),
    )
    await state.update_data(
        message_id=message.message_id,
        chat_id=message.from_user.id,
    )
    await state.set_state(BroadcastStatesGroup.add_button)


async def add_button(call: CallbackQuery, bot: Bot, state: FSMContext):
    if call.data == 'add_button':
        await call.message.answer(
            'Отправьте текст для кнопки',
            reply_markup=None,
        )
        await state.set_state(BroadcastStatesGroup.get_button_text)
    elif call.data == 'no_button':
        await call.message.edit_reply_markup(reply_markup=None)
        data = await state.get_data()
        message_id = int(data.get('message_id'))
        chat_id = int(data.get('chat_id'))
        await confirm(call.message, bot, message_id, chat_id)
        await state.set_state(BroadcastStatesGroup.get_button_url)
    await call.answer()


async def get_text_button(message: Message, state: FSMContext):
    await state.update_data(text_button=message.text)
    await message.answer('Отправьте ссылку')
    await state.set_state(BroadcastStatesGroup.get_button_url)


async def get_button_url(message: Message, bot: Bot, state: FSMContext):
    await state.update_data(url_button=message.text)
    added_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(await state.get_data()).get('text_button'),
                    url=f'{message.text}',
                ),
            ],
        ],
    )
    data = await state.get_data()
    message_id = int(data.get('message_id'))
    chat_id = int(data.get('chat_id'))
    await confirm(message, bot, message_id, chat_id, added_keyboard)


async def confirm(
    message: Message,
    bot: Bot,
    message_id: int,
    chat_id: int,
    reply_markup: InlineKeyboardMarkup = None,
):
    await bot.copy_message(
        chat_id,
        chat_id,
        message_id,
        reply_markup=reply_markup,
    )
    await message.answer(
        'Подтвердить рассылку',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Подтвердить',
                        callback_data='confirm_broadcast',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='Отклонить',
                        callback_data='cancel_broadcast',
                    ),
                ],
            ],
        ),
    )


async def broadcast_confirmation(
    call: CallbackQuery,
    bot: Bot,
    state: FSMContext,
):
    data = await state.get_data()
    message_id = int(data.get('message_id'))
    chat_id = int(data.get('chat_id'))
    text_button = data.get('text_button')
    url_button = data.get('url_button')
    success_send, failed_send = 0, 0
    if call.data == 'confirm_broadcast':
        await call.message.edit_text('Начинаю рассылку...')
        db_sess = db_session.create_session()
        groups = db_sess.query(Group).all()
        keyboard = make_keyboard(text_button, url_button)
        for group in groups:
            try:
                await bot.copy_message(
                    group.telegram_id,
                    chat_id,
                    message_id,
                    reply_markup=keyboard.as_markup()
                    if keyboard is not None
                    else keyboard,
                )
                success_send += 1
            except Exception:
                failed_send += 1
        await call.message.answer(
            f'Доставлено: {success_send}.\nНе доставлено: {failed_send}',
        )
    elif call.data == 'cancel_broadcast':
        await call.message.edit_text('Рассылка отменена')
    await state.clear()


def make_keyboard(text_button: str, url_button: str):
    keyboard = None
    if text_button and url_button:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=text_button, url=url_button)
        keyboard.adjust(1)
    return keyboard
