import logging
from telegram.ext import Updater

# Импортируем токен из другого файла safety_key.py.
from safety_key import TOKEN


# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
    filename="./logs/tfinance_main.log")

logger = logging.getLogger(__name__)


def main():
    # Создаём объект updater.
    updater = Updater(TOKEN)

    # Обработка сообщений.
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
