# ----------------------------------------- Основной файл приложения ----------------------------------------- #
# --------------- Импорт необходимых библиотек, функций, классов --------------- #
# Встроенные библиотеки.
import logging
import os

# Для работы со временем.
import datetime
import pytz

# Работа с telegram-bot-api.
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler

# Работа с акциями (загрузка, вывод, проверка, игра, визуализация).
from graphics.visualize import do_stock_image, pdr, \
    check_stock_prices
from stock import check_stock, load_stocks, get_all_stocks

from database import Database  # ORM (БД с данными о пользователях).
from items import User  # Класс пользователя.

# Импортируем TOKEN из безопасного места
from safety_key import TOKEN

# Запускаем логирование
if not os.path.exists(f'{os.getcwd()}/logs'):
    os.mkdir(f'{os.getcwd()}/logs')
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
    filename=f"{os.getcwd()}/logs/tfinance_main.log")
logger = logging.getLogger(__name__)


# Отправка всех акций из заданного диапазона (start, end).
def send_stocks(update, start, end, templates):
    msg = ''
    for i in range(start, end):
        msg += templates['stocks'][i] + ', '
    update.message.reply_text(msg)


# Получение списка необходимых акций по команде /stocks [args]. Обработчик команды /stocks.
def get_list_stocks(update, context):
    try:
        templates = load_stocks('stocks.json')  # Загружаем список всех акций

        # Проверка на наличие аргументов
        if context.args[0] == 'all':
            # Большим сообщением все сразу не отправится, поэтому разделяем на 3 поменьше.
            send_stocks(update, 0, 700, templates)
            send_stocks(update, 700, 1400, templates)
            send_stocks(update, 1400, 2100, templates)
        elif context.args[0].isdigit():  # Если аргумент - число, отсылаем первые n акций.
            numb = int(context.args[0])
            if numb > 700:
                while numb > 700:
                    numb = 700
                    send_stocks(update, 0, numb, templates)
                    numb = int(context.args[0]) - 700
            send_stocks(update, 0, numb, templates)
        else:  # Если аргумент - строка, выводим все акции на первую букву строки.
            message = ''
            for el in templates['stocks']:
                if el[0].lower() == context.args[0].lower():
                    message += el + ', '
            update.message.reply_text(message)
    except (IndexError, ValueError):
        update.message.reply_text("Неверный способ ввода. /help")


# Обработчик команды /stock [stock_index]. Визуализирует график и отправляет его в прямом порядке.
def get_stock_image(update, context):
    try:
        update.message.reply_photo(do_stock_image(context.args[0]))
    except (IndexError, ValueError):
        update.message.reply_text("Неверный способ ввода. /stock [индекс акции]. Например: /stock AAPL")
    except pdr._utils.RemoteDataError:
        update.message.reply_text("Такой акции не было найдено в данных Yahoo Finance.")


# Обработчик команды /start. Добавляет пользователя в БД, тем самым открывая ему доступ к командам.
def start(update, _):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    Database('data.db').add_user(user)
    update.message.reply_text(f"Привет, {user.first_name}! Теперь доступ к командам открыт.")


# Обработчик команды /help. ToDo: Сделать вывод всех команд и пояснение к ним.
def help(update, _):
    update.message.reply_text("/stocks [количество акций] Например: /stocks 100 - посмотреть первые 100 акций\n"
                              "/stocks all - посмотреть все акции на бирже\n"
                              "/stocks [буква алфавита] Например: /stocks A -"
                              "посмотреть все акции,название которых начинается с 'A'\n"
                              "/follow [stock_name] - добавить акцию в избранное\n"
                              "/unfollow [stock_name] - удалить акцию из избранного\n"
                              "/favourites - посмотреть список избранных акций\n")


# Обработчик команды /favourites. Отправляет список любимых акций.
def favourites(update, _):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    stocks = Database('data.db').get_favourites_stocks(user)
    if stocks and stocks[0]:
        update.message.reply_text(', '.join(stocks[0].split()))
    else:
        update.message.reply_text('У вас нет избранных акций')


# Обработчик команды /follow. Возможность подписываться на другие акции.
def follow(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    if context.args[0]:
        context.args[0] = context.args[0].upper()
        if Database('data.db').check_favourites_stocks(user, context.args[0]):
            update.message.reply_text('Акция уже в избранном')
        else:
            if check_stock(context.args[0]):
                Database('data.db').add_favourites_stocks(user, context.args[0])
                update.message.reply_text('Акция добавлена в избранное')
            else:
                update.message.reply_text('Акция не найдена')
    else:
        update.message.reply_text('Неверный способ ввода. /follow [индекс акции]. Например: /follow AAPL')


# Обработчик команды /unfollow. Возможность отписки от акций.
def unfollow(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    if context.args[0]:
        context.args[0] = context.args[0].upper()
        if not Database('data.db').check_favourites_stocks(user, context.args[0]):
            update.message.reply_text('Акции нет в избранном')
        else:
            Database('data.db').remove_favourites_stock(user, context.args[0])
            update.message.reply_text('Акция удалена из избранного')
    else:
        update.message.reply_text('Неверный способ ввода. /unfollow [индекс акции].')


# Ежедневная рассылка избранных акций.
def notify_assignees(context):
    # Перебираем всех пользователей и рассылаем каждому курсы их избранных акций.
    for user in Database('data.db').get_users():
        if Database('data.db').check_user_daily_notify(user.id):
            if user.favourites_stocks:
                for i in user.favourites_stocks.split():
                    try:
                        context.bot.send_photo(chat_id=user.id, photo=do_stock_image(i))
                    except Exception as e:
                        print(e)


# Обработчик команды /daily. Включение/выключение ежедневной рассылки.
def daily(update, _):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    Database('data.db').add_user(user)
    if Database('data.db').check_user_daily_notify(user):
        update.message.reply_text(f'Ежедневная рассылка выключена')
    else:
        update.message.reply_text(f'Ежедневная рассылка включена')
    Database('data.db').user_daily_notify(user)


# Обработчик команды /stats. Вывод статистики пользователя из БД.
def stats(update, _):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    data = Database('data.db').read_info(user)
    try:
        update.message.reply_text(f'UserName: {data[0]}\nИзбранные акции:'
                                  f' {", ".join(data[1].split()) if data[1] else None}'
                                  f'\nОчки, заработанные в игре: {data[2]}')
    except TypeError:
        update.message.reply_text('Вас нет в бд, запустите команду /start чтобы исправить ошибку')


# Обработчик команды /game [stock_index]. Основное меню игры с предугадыванием.
def game_menu(update, context):
    try:
        if not context.args:
            update.message.reply_text("Неправильно введена команда! Попробуйте: /game [индекс акции]")
            return ConversationHandler.END

        user_data = update.effective_user
        user = User(user_data.to_dict())
        data = Database('data.db')
        message_id = str(int(update.message.message_id) + 2)  # Сохраняем id сообщения для возможности одновременной
        # игры на многих акциях. Прибавляем 2 т.к. отправляем 2 сообщения: фото и приписку к нему с клавиатурой.

        data.select_stock(user, f"{context.args[0]}:{message_id}")  # Запоминаем, что акция была выбрана.

        if Database('data.db').check_prediction_stock(user, context.args[0]):  # Избегаем читерства.
            update.message.reply_text("Прогноз на эту акцию уже установлен.")
            return ConversationHandler.END

        # Создание клавиатуры и отправка ответа.
        keyboard = [[
            InlineKeyboardButton("Повышение", callback_data=str(1)),
            InlineKeyboardButton("Понижение", callback_data=str(2))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_photo(photo=do_stock_image(context.args[0]))
        update.message.reply_text(text=f"Предугадайте курс {context.args[0]} на завтра.", reply_markup=reply_markup)
    except pdr._utils.RemoteDataError:
        update.message.reply_text(text="Такой акции не было найдено в данных Yahoo Finance.")
        return ConversationHandler.END
    except TypeError:
        update.message.reply_text('Вас нет в бд, запустите команду /start чтобы исправить ошибку')
    except KeyError:
        update.message.reply_text(text="Такой акции не было найдено в данных Yahoo Finance.")
        return ConversationHandler.END

    return 1  # Возвращаем 1, чтобы показать ConversationHandler'у состояние, в котором находимся.


# Кнопка повышения акции.
def higher_game(update, _):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    data = Database('data.db')

    # Обработка и ответ на колл-бэк.
    query = update.callback_query
    query.answer()

    message_id = query.message.message_id  # Получаем id сообщения, для нахождения нужной сессии игры.
    data.add_prediction(user, data.get_selected_stock(user, message_id), 'up')  # Устанавливаем прогноз на акцию.
    data.remove_selected_stock(user, message_id)  # Удаляем акцию из выбранных.

    query.edit_message_text(text="Предсказание установлено на повышение")  # Редактируем сообщение с клавиатурой.


# Кнопка понижения акции.
def lower_game(update, _):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    data = Database('data.db')

    # Обработка и ответ на колл-бэк.
    query = update.callback_query
    query.answer()

    message_id = query.message.message_id  # Получаем id сообщения, для нахождения нужной сессии игры.
    data.add_prediction(user, data.get_selected_stock(user, message_id), 'down')  # Устанавливаем прогноз на акцию.
    data.remove_selected_stock(user, message_id)  # Удаляем акцию из выбранных.

    query.edit_message_text(text="Предсказание установлено на понижение")  # Редактируем сообщение с клавиатурой.


# Подсчет результатов игры.
def game_results(context):
    db = Database('data.db')
    for user in db.get_users():
        for i in user.prediction.split():
            # Проверка прогноза
            try:
                if i.split(":")[-1] == 'up':
                    if check_stock_prices(i.split(":")[0]):
                        context.bot.send_message(chat_id=user.id, text=f"Прогноз {i.split(':')[0]} был верным. "
                                                                       f"\nВы получили 1 очко. "
                                                                       f"\nПосмотреть кол-во очков можно, "
                                                                       f"использовав /stats.")
                        db.add_point(user)
                    else:
                        context.bot.send_message(chat_id=user.id, text=f"Прогноз {i.split(':')[0]} был неверным.")
                else:
                    if not check_stock_prices(i.split(":")[0]):
                        context.bot.send_message(chat_id=user.id, text=f"Прогноз {i.split(':')[0]} был верным. "
                                                                       f"\nВы получили 1 очко. "
                                                                       f"\nПосмотреть кол-во очков можно, "
                                                                       f"использовав /stats.")
                        db.add_point(user)
                    else:
                        context.bot.send_message(chat_id=user.id, text=f"Прогноз {i.split(':')[0]} был неверным.")
            except KeyError:
                # Если биржа перестанет работать, по непонятным нам причинам, то удалятся прошлые прогнозы.
                db.delete_predictions(user)
                context.bot.send_message(chat_id=user.id, text=f"На данный момент к бирже нет доступа. "
                                                               f"Прогноз на акцию {i.split(':')[0]} был отменен.")
        # Удаляем пройденные прогнозы
        db.delete_predictions(user)
        user.prediction = db.get_predictions(user)


# Основной цикл, активирующийся при запуске.
def main():
    # Получение и сохранение списка всех акций в stocks.json.
    try:
        get_all_stocks()
    except Exception as e:
        logging.error(e)

    # Создаём объект updater.
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue

    # Ежедневные задачи.
    job_queue.run_daily(notify_assignees, datetime.time(hour=8, tzinfo=pytz.timezone('Europe/Moscow')))
    job_queue.run_daily(game_results, datetime.time(hour=3, tzinfo=pytz.timezone('Europe/Moscow')))

    # ConversationHandler для игры.
    game_handler = ConversationHandler(entry_points=[CommandHandler("game", game_menu)],
                                       states={1: [CallbackQueryHandler(higher_game, pattern=f"^1$"),
                                                   CallbackQueryHandler(lower_game, pattern=f"^2$")]},
                                       fallbacks=[CommandHandler("game", game_menu)])
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


if __name__ == '__main__':
    main()
