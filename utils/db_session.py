import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext import declarative

__all__ = []

SqlAlchemyBase = declarative.declarative_base()

__factory = None


def global_init(
    user='postgres',
    port=5432,
    host='localhost',
    db_name='postgres',
    password='',
):
    global __factory

    if __factory:
        return

    connection_address = (
        f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}'
    )
    engine = sqlalchemy.create_engine(connection_address)
    __factory = orm.sessionmaker(bind=engine)

    from utils import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> orm.Session:
    global __factory
    return __factory()
