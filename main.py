# -------------------------- Основной файл приложения -------------------------- #
# --------------- Импорт необходимых библиотек, функций, классов --------------- #
# Встроенные библиотеки.
import logging
import os
import warnings

# Для работы со временем.
import datetime
from pathlib import Path

import pytz

# Работа с telegram-bot-api.
from telegram.ext import (
    Updater, CommandHandler, ConversationHandler, CallbackQueryHandler,
)

# Работа с акциями (загрузка, вывод, проверка, игра, визуализация, рассылка).
from blast import notify_assignees, daily
from functions import create_user

import pandas_datareader as pdr
from graphics.visualize import do_stock_image
from stock import check_stock, load_stocks, get_all_stocks
# ORM (БД с данными о пользователях).
from database import Database
from game import game_menu, higher_game, lower_game, game_results

# Импортируем TOKEN из безопасного места
from safety_key import TOKEN

# Запускаем логирование
logs_path = Path(f"{os.getcwd()}/logs")
if not logs_path.exists():
    logs_path.mkdir(exist_ok=True)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARNING,
    filename=f"{os.getcwd()}/logs/tfinance_main.log")
logger = logging.getLogger(__name__)

# Отключаем предупреждения пользователей библиотек
warnings.simplefilter("ignore")


# Отправка всех акций из заданного диапазона (start, end).
def send_stocks(update, start, end, templates):
    msg = ""
    for i in range(start, end):
        msg += templates["stocks"][i] + ", "
    update.message.reply_text(msg)


# Получение списка необходимых акций по команде /stocks [args].
# Обработчик команды /stocks.
def get_list_stocks(update, context):
    try:
        templates = load_stocks("stocks.json")  # Загружаем список всех акций

        # Проверка на наличие аргументов
        if context.args[0] == "all":
            # Большим сообщением все сразу не отправится,
            # поэтому разделяем на 3 поменьше.
            send_stocks(update, 0, 700, templates)
            send_stocks(update, 700, 1400, templates)
            send_stocks(update, 1400, 2100, templates)
        # Если аргумент - число, отсылаем первые n акций.
        elif context.args[0].isdigit():
            numb = int(context.args[0])
            if numb > 700:
                while numb > 700:
                    numb = 700
                    send_stocks(update, 0, numb, templates)
                    numb = int(context.args[0]) - 700
            send_stocks(update, 0, numb, templates)
        # Если аргумент - строка, выводим все акции на первую букву строки.
        else:
            message = []
            for el in templates["stocks"]:
                if el[0].lower() == context.args[0].lower()[0]:
                    message.append(el)
            update.message.reply_text(", ".join(message))
    except (IndexError, ValueError):
        update.message.reply_text("Неверный способ ввода. /help")


# Обработчик команды /stock [stock_index].
# Визуализирует график и отправляет его в прямом порядке.
def get_stock_image(update, context):
    try:
        if context.args[0]:
            update.message.reply_photo(do_stock_image(context.args[0]))
        else:
            raise ValueError
    except (IndexError, ValueError):
        update.message.reply_text(
            "Неверный способ ввода. /stock [индекс акции]. Например: /stock AAPL",
        )
    except pdr._utils.RemoteDataError:
        update.message.reply_text(
            "Такой акции не было найдено в данных Yahoo Finance.",
        )


# Обработчик команды /start.
# Добавляет пользователя в БД, тем самым открывая ему доступ к командам.
def start(update, _):
    user = create_user(update)
    db.add_user(user)
    update.message.reply_text(
        f"Привет, {user.first_name}! Теперь доступ к командам открыт.\n"
        f"Введите /help для просмотра списка команд.",
    )


# Список команд.
def help(update, _):
    update.message.reply_text(
        """
/stock [stock_name] - посмотреть график цены акции за 30 дней
Например /stock AAPL - посмотреть график цены акции Apple за 30 дней
/stocks [количество акций]
Например: /stocks 100 - посмотреть первые 100 акций
/stocks all - посмотреть все акции на бирже
/stocks [буква алфавита]
Например: /stocks A - посмотреть все акции,название которых начинается с 'A'

/follow [stock_name] - добавить акцию в избранное
/unfollow [stock_name] - удалить акцию из избранного
/favourites - посмотреть список избранных акций

/daily - установить ежедневную рассылку избранных акций
/stats - посмотреть собственную статистику
/game [stock_name] - начать игру с прогнозом выбранной акции
        """,
    )


# Отправляет список любимых акций.
def favourites(update, _):
    user = create_user(update)
    stocks = db.get_favourites_stocks(user)
    if stocks and stocks[0]:
        update.message.reply_text(", ".join(stocks[0].split()))
    else:
        update.message.reply_text("У вас нет избранных акций")


# Возможность подписываться на другие акции.
def follow(update, context):
    user = create_user(update)
    if context.args and context.args[0]:
        context.args[0] = context.args[0].upper()
        if db.check_favourites_stocks(user, context.args[0]):
            update.message.reply_text("Акция уже в избранном")
        else:
            if check_stock(context.args[0]):
                db.add_favourites_stocks(user, context.args[0])
                update.message.reply_text("Акция добавлена в избранное")
            else:
                update.message.reply_text("Акция не найдена")
    else:
        update.message.reply_text(
            "Неверный способ ввода. /follow [индекс акции]. Например: /follow AAPL",
        )


# Возможность отписки от акций.
def unfollow(update, context):
    user = create_user(update)
    if context.args and context.args[0]:
        context.args[0] = context.args[0].upper()
        if not db.check_favourites_stocks(user, context.args[0]):
            update.message.reply_text("Акции нет в избранном")
        else:
            db.remove_favourites_stock(user, context.args[0])
            update.message.reply_text("Акция удалена из избранного")
    else:
        update.message.reply_text("Неверный способ ввода. /unfollow [индекс акции].")


# Вывод статистики пользователя из БД.
def stats(update, _):
    user = create_user(update)
    data = db.read_info(user)
    try:
        favourites_string = ", ".join(data[1].split()) if data[1] else "Нет"
        update.message.reply_text(
            f"""
UserName: {data[0]}
Избранные акции: {favourites_string}
Очки, заработанные в игре: {data[2]}
            """,
        )
    except TypeError:
        update.message.reply_text(
            "Вас нет в бд, запустите команду /start чтобы исправить ошибку",
        )


# Основной цикл, активирующийся при запуске.
def main():
    # Получение и сохранение списка всех акций в stocks.json.
    try:
        get_all_stocks()
    except Exception as e:
        logging.error(e)

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue

    # Ежедневные задачи.
    job_queue.run_daily(
        notify_assignees, datetime.time(
            hour=8, tzinfo=pytz.timezone("Europe/Moscow"),
        ),
    )
    job_queue.run_daily(
        game_results, datetime.time(
            hour=3, tzinfo=pytz.timezone("Europe/Moscow"),
        ),
    )

    # Обработчик для игры.
    game_handler = ConversationHandler(
        entry_points=[CommandHandler("game", game_menu)],
        states={1: [CallbackQueryHandler(higher_game, pattern="^1$"),
                    CallbackQueryHandler(lower_game, pattern="^2$")]},
        fallbacks=[CommandHandler("game", game_menu)],
    )
    dispatcher.add_handler(game_handler)

    # Регистрируем обработчик команд.
    dispatcher.add_handler(CommandHandler("daily", daily))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("favourites", favourites))
    dispatcher.add_handler(CommandHandler("follow", follow))
    dispatcher.add_handler(CommandHandler("unfollow", unfollow))
    dispatcher.add_handler(CommandHandler("stock", get_stock_image))
    dispatcher.add_handler(CommandHandler("stocks", get_list_stocks))
    dispatcher.add_handler(CommandHandler("stats", stats))

    # Обработка сообщений.
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    db: Database = Database("data.db")
    main()
