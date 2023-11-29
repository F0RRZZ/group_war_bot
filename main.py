import asyncio
from datetime import datetime as dt
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from apsched import send_message_cron
import broadcast_handlers as bh
from handlers import router
from states import BroadcastStatesGroup

__all__ = []

load_dotenv()


async def main():
    bot = Bot(token=os.getenv('TOKEN'))
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.add_job(
        send_message_cron,
        trigger='cron',
        hour=22,
        start_date=dt.now(),
    )
    scheduler.start()
    dp = Dispatcher(storage=MemoryStorage())
    await bot.delete_webhook()
    dp.message.register(
        bh.broadcast,
        Command('start_broadcast'),
    )
    dp.message.register(
        bh.get_broadcast_message,
        BroadcastStatesGroup.get_message,
    )
    dp.callback_query.register(
        bh.add_button,
        BroadcastStatesGroup.add_button,
    )
    dp.message.register(
        bh.get_text_button,
        BroadcastStatesGroup.get_button_text,
    )
    dp.message.register(
        bh.get_button_url,
        BroadcastStatesGroup.get_button_url,
    )
    dp.callback_query.register(
        bh.broadcast_confirmation,
        F.data.in_(['confirm_broadcast', 'cancel_broadcast']),
    )
    dp.include_router(router)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())
