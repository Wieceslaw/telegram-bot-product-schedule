import telebot
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.custom_filters import SimpleCustomFilter
from telebot.storage import StateMemoryStorage

from apscheduler.schedulers.background import BackgroundScheduler

from datetime import datetime, timedelta

from settings import *
from data import db_session
from data.product_model import Product


# создаем хранилище состояний бота (хранит промежуточные данные, пример: имя продука, пока он еще не добавлен)
state_storage = StateMemoryStorage()
# сам объект бота (для него нужен токен - уникальный идентификатор, который можно получить у телеграма для своего бота)
bot = telebot.TeleBot(TOKEN, state_storage=state_storage)

# создаем класс состояний для нашего диалога с пользователем, в нем 5 стадий: спрашиваем имя, потом цену и так далее
class ProductStates(StatesGroup):
    name = State()
    price = State()
    year = State()
    month = State()
    day = State()


@bot.message_handler(commands=["start"])
def send_welcome(message):
    """
    Обработчик новых пользователей, приветствие (команда /start)
    """
    msg = bot.send_message(message.chat.id, "Привет!")


@bot.message_handler(commands=["help"])
def add_product(message):
    """
    Команда /help, выводит вспомогательное сообщение с краткой справкой о командах
    """
    bot.send_message(
        message.chat.id,
        "Для добавления товара введите /add\nДля отменя добавления товара введите /cancel",
    )


@bot.message_handler(commands=["list"])
def product_list(message):
    """
    Вывести список товаров
    """
    session = db_session.create_session()
    # получаем все продукты, которые были добавлены из нашего чата
    products = session.query(Product).filter(Product.chat_id == message.chat.id)
    # формируем сообщение
    product_list = "Список ваших товаров:\n" + "\n\n".join(
        [product.__repr__() for product in products]
    )
    bot.send_message(message.chat.id, product_list)


@bot.message_handler(state="*", commands="cancel")
def cancel_addition(message):
    """
    Отмена добавления товара
    """
    bot.send_message(message.chat.id, "Добавление товара отменено")
    # удаляем текущее состояние для добавления товара
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(commands=["add"])
def add_product(message):
    """
    Команда для добавления нового товара
    """
    # устанавливаем текущее состояние - ProductStates.name (опрос имени)
    bot.set_state(message.from_user.id, ProductStates.name, message.chat.id)
    # отправляем сообщение пользователю, чтобы он ввел название
    bot.send_message(message.chat.id, "Введите название товара")


@bot.message_handler(state=ProductStates.name)
def ask_price(message):
    """
    Получили имя, получаем цену
    """
    bot.send_message(message.chat.id, "Введите цену товара")
    bot.set_state(message.from_user.id, ProductStates.price, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["name"] = message.text


@bot.message_handler(state=ProductStates.price, is_price=True)
def ask_year(message):
    """
    Цена верная, получаем год
    """
    bot.send_message(message.chat.id, "Назовите год истечения срока годности")
    bot.set_state(message.from_user.id, ProductStates.year, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["price"] = float(message.text)


@bot.message_handler(state=ProductStates.price, is_price=False)
def price_incorrect(message):
    """
    Неверная цена (отрицательная / не число)
    """
    bot.send_message(
        message.chat.id, "Кажется, вы ввели неверную цену. Введите цену снова."
    )


@bot.message_handler(state=ProductStates.year, is_year=True)
def ask_month(message):
    """
    Год верный, получаем месяц
    """
    bot.send_message(message.chat.id, "Назовите месяц истечения срока годности")
    bot.set_state(message.from_user.id, ProductStates.month, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["year"] = int(message.text)


@bot.message_handler(state=ProductStates.year, is_year=False)
def year_incorrect(message):
    """
    Неверный год (отрицательный / не целое число)
    """
    bot.send_message(
        message.chat.id, "Кажется, вы ввели неверный год. Введите год снова."
    )


@bot.message_handler(state=ProductStates.month, is_month=True)
def ask_day(message):
    """
    Месяц верный, получаем день
    """
    bot.send_message(message.chat.id, "Назовите день истечения срока годности")
    bot.set_state(message.from_user.id, ProductStates.day, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["month"] = int(message.text)


@bot.message_handler(state=ProductStates.month, is_month=False)
def month_incorrect(message):
    """
    Неверный месяц (отрицательный / не целое число)
    """
    bot.send_message(
        message.chat.id, "Кажется, вы ввели неверный месяц. Введите месяц снова."
    )


@bot.message_handler(state=ProductStates.day, is_day=True)
def ready_for_answer(message):
    """
    Выводим результат
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["day"] = int(message.text)
        session = db_session.create_session()
        product = Product()
        product.chat_id = message.chat.id
        product.name = data["name"]
        product.price = data["price"]
        product.date = datetime(data["year"], data["month"], data["day"])
        session.add(product)
        session.commit()
        bot.send_message(message.chat.id, product, parse_mode="html")

    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(state=ProductStates.day, is_day=False)
def month_incorrect(message):
    """
    Неверный день (отрицательный / не целое число)
    """
    bot.send_message(
        message.chat.id, "Кажется, вы ввели неверный день. Введите день снова."
    )


# Добавляем фильтры


class PriceFilter(SimpleCustomFilter):
    """
    Фильтр цены, берем только положительное число
    """

    key = "is_price"

    def check(self, message):
        try:
            if float(message.text) > 0:
                return True
        except ValueError:
            pass
        return False


class YearFilter(SimpleCustomFilter):
    """
    Фильтр года, берем только положительное целое число
    """

    key = "is_year"

    def check(self, message):
        try:
            if message.text.isdigit() and int(message.text) > 0:
                return True
        except ValueError:
            pass
        return False


class MonthFilter(SimpleCustomFilter):
    """
    Фильтр месяца, берем только положительное целое число в пределах [1, 12]
    """

    key = "is_month"

    def check(self, message):
        try:
            if message.text.isdigit() and 12 >= int(message.text) > 0:
                return True
        except ValueError:
            pass
        return False


class DayFilter(SimpleCustomFilter):
    """
    Фильтр дней месяца, берем только положительные целые числа в пределах [1, 31]
    """

    key = "is_day"

    def check(self, message):
        try:
            if message.text.isdigit() and 32 > int(message.text) > 0:
                return True
        except ValueError:
            pass
        return False


# Добавляем наши фильтры
bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())
bot.add_custom_filter(PriceFilter())
bot.add_custom_filter(YearFilter())
bot.add_custom_filter(MonthFilter())
bot.add_custom_filter(DayFilter())


def notify():
    """
    Функция для инормирования о сроках годности
    """
    # подключаемся к базе данных
    session = db_session.create_session()
    # получаем все продукты из базы данных
    products = session.query(Product)
    # получаем текущую дату/время
    now = datetime.now()
    for product in products:
        # если о продукте уже пришло уведомление, то ничего не делаем
        if not product.notified:
            message = None
            if product.date.date() == now.date(): # если срок годности кончается сегодня
                message = f"Добрый день! У вашего продукта {product.name} заканчивается срок годность сегодня."
            elif product.date - now <= timedelta(days=1) and product.date > now: # если срок годности кончается завтра
                message = f"Добрый день! У вашего продукта {product.name} заканчивается срок годность, у вас остался день до его окончания."
            elif product.date < now: # если срок годности уже закончился (например, был добавлен уже просроченный товар)
                message = f"Добрый день! У вашего продукта {product.name} срок годности уже закончился."
            if message:
                # отправляем напоминание
                bot.send_message(
                    chat_id=product.chat_id,
                    text=message,
                )
                # устанавливаем свойство продукта, что напоминание о нем уже было прислано
                product.notified = True
    # сохраняем изменения в базе данных
    session.commit()


def main():
    """
    входная точка в программу
    """
    # запускаем фоновый планировщик
    scheduler = BackgroundScheduler()
    # передаем функцию, которую будем вызывать (напоминание) каждые 10 секунд
    scheduler.add_job(notify, "cron", second="*/10")
    # запускаем планировщик
    scheduler.start()

    # инициализируем базу данных
    db_session.global_init(DB_PATH)
    # запускаем бота
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()
