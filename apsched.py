import os

from aiogram import Bot
from dotenv import load_dotenv

from models import User
from utils import db_session

load_dotenv()


db_session.global_init(
    user=os.getenv('DB_USER'),
    port=os.getenv('DB_PORT'),
    host=os.getenv('DB_HOST'),
    db_name=os.getenv('DB_NAME'),
    password=os.getenv('DB_PASSWORD'),
)


async def change_increase_and_raid_status():
    db_sess = db_session.create_session()
    for user in db_sess.query(User).all():
        user.increased_today = False
        user.raided_today = False
    db_sess.commit()
