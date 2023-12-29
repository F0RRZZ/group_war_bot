import asyncio
from datetime import datetime as dt

from aiogram import F
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import apsched
import broadcast_handlers as bh
from config import bot, dp
from handlers import router
from states import BroadcastStatesGroup

__all__ = []


async def main():
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.add_job(
        apsched.change_increase_and_raid_status,
        trigger='cron',
        hour=22,
        start_date=dt.now(),
    )
    scheduler.add_job(
        apsched.reset_stats,
        trigger='cron',
        day=1,
        hour=0,
        minute=0,
        start_date=dt.now(),
    )
    scheduler.start()
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
