import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

__factory = None


"""
Код достаточно сложный
В оффициальной документации библиотеки для работы с базой данных рекомендуется именно так ее инициализировать
"""


def global_init(db_file):
    """
    Функция для инициализации базы данных
    """

    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Must specify database file.")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"[INFO]: Database {conn_str} connected")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    """
    Функция для получения сессии для работы с базой данных
    """
    global __factory
    return __factory()