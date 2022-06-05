import sqlalchemy

from .db_session import SqlAlchemyBase

"""
Модель нашего продукта в базе данных (фактически таблица с продуктами и его характеристиками)
"""

class Product(SqlAlchemyBase):
    __tablename__ = 'product'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    chat_id = sqlalchemy.Column(sqlalchemy.BigInteger, nullable=False)
    price = sqlalchemy.Column(sqlalchemy.FLOAT, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    notified = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    def __repr__(self) -> str:
        """
        Функция, которая определяет то, как будет выглядеть наш товар при печати, например - print(product) вернет это сообщение
        """
        return f"""Товар:
Название - {self.name}
Цена - {self.price}
Срок годности - {self.date.strftime('%d.%m.%Y')}"""