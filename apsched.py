import os

from dotenv import load_dotenv

from models import SeasonWinner, User
import queries
from utils import db_session

load_dotenv()

__all__ = [
    'change_increase_and_raid_status',
    'reset_stats',
]

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


async def reset_stats():
    db_sess = db_session.create_session()
    winners = queries.get_season_winners(db_sess)
    for winner in winners:
        season_winner = SeasonWinner(
            telegram_id=winner.telegram_id,
            username=winner.username,
            first_name=winner.first_name,
            last_name=winner.last_name,
            soldiers_count=winner.soldiers_count,
            wins=winner.wins,
            defeats=winner.defeats,
        )
        db_sess.add(season_winner)
    for user in db_sess.query(User).all():
        user.soldiers_count = 0
    db_sess.commit()
