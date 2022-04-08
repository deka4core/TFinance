import logging
import json

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


def send_stocks(update, start, end, templates):
    msg = ''
    for i in range(start, end):
        msg += templates['stocks'][i] + ', '
    update.message.reply_text(msg)


def get_list_stocks(update, context):
    try:
        with open('stocks.json') as f:
            templates = json.load(f)
        if context.args[0] == 'all':
            send_stocks(update, 0, 700, templates)
            send_stocks(update, 700, 1400, templates)
            send_stocks(update, 1400, 2100, templates)
        elif context.args[0].isdigit():
            numb = int(context.args[0])
            if numb > 700:
                while numb > 700:
                    numb = 700
                    send_stocks(update, 0, numb, templates)
                    numb = int(context.args[0]) - 700
            send_stocks(update, 0, numb, templates)
        else:
            message = ''
            for el in templates['stocks']:
                if el[0] == context.args[0]:
                    message += el + ', '
            update.message.reply_text(message)
    except (IndexError, ValueError):
        update.message.reply_text("Неверный способ ввода. /help")



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
    update.message.reply_text("/stocks [количество акций] Например: /stocks 100 - посмотреть первые 100 акций\n"
                              "/stocks all - посмотреть все акции на бирже\n"
                              "/stocks [буква алфавита] Например: /stocks A - посмотреть все акции, "
                              "название которых начинается с 'A'")


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

            
def stats(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    data = Database('data.db').read_info(user)
    try:
        update.message.reply_text(f'UserName: {data[0]}\nИзбранные акции: {data[1]}\nОчки, заработанные в игре: {data[2]}')
    except TypeError:
        update.message.reply_text('Вас нет в бд, запустите команду /start чтобы исправить ошибку')

            
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
    dispatcher.add_handler(CommandHandler("stocks", get_list_stocks))
    dispatcher.add_handler(CommandHandler("stats", stats))
    # Обработка сообщений.
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
