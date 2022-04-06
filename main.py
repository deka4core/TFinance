import logging

from graphics.visualize import pdr
from telegram.ext import Updater, CommandHandler

# Импортируем токен из другого файла safety_key.py.
from safety_key import TOKEN


# Запускаем логирование
from graphics.visualize import do_stock_image
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


def main():
    # Создаём объект updater.
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Регистрируем обработчик команд.
    dispatcher.add_handler(CommandHandler("stock", get_stock_image))

    # Обработка сообщений.
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
