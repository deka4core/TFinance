import logging

from database import Database
from graphics.visualize import pdr
from telegram.ext import Updater, CommandHandler

from items import User

# Импортируем токен из другого файла safety_key.py.
from safety_key import TOKEN

from graphics.visualize import do_stock_image

# Запускаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
    filename="./logs/tfinance_main.log")
logger = logging.getLogger(__name__)



# Обработчик команды /stock [stock_index]
def get_stock_image(update, context):
    try:
        update.message.reply_photo(do_stock_image(context.args[0]))
    except (IndexError, ValueError):
        update.message.reply_text("Неверный способ ввода. /stock [индекс акции]. Например: /stock AAPL")
    except pdr._utils.RemoteDataError:
        update.message.reply_text("Такой акции не было найдено в данных Yahoo Finance.")


def start(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    Database('data.db').add_user(user)
    update.message.reply_text(f"Привет {user.first_name}!")


def help(update, context):
    update.message.reply_text("Я пока не умею помогать...")


def favourites(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    stocks = Database('data.db').get_favourites_stocks(user)
    if stocks:
        update.message.reply_text(', '.join(stocks))
    else:
        update.message.reply_text('У вас нет избранных акций')


def follow(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    if context.args[0]:
        if Database('data.db').check_favourites_stocks(user, context.args[0]):
            update.message.reply_text('Акция уже в избранном')
        else:
            Database('data.db').add_favourites_stocks(user, context.args[0])
            update.message.reply_text('Акция добавлена в избранное')


def main():
    # Создаём объект updater.
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    # Регистрируем обработчик команд.
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("favourites", favourites))
    dispatcher.add_handler(CommandHandler("follow", follow))
    dispatcher.add_handler(CommandHandler("stock", get_stock_image))
    # Обработка сообщений.
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
