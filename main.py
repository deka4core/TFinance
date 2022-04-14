import logging
import datetime
import pytz
import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from graphics.visualize import pdr, check_stock_prices
from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters
from items import User
# Импортируем токен из другого файла safety_key.py.
from safety_key import TOKEN
from graphics.visualize import do_stock_image
from stock import load_stocks, get_all_stocks, check_stock

# Запускаем логирование
if not os.path.exists(f'{os.getcwd()}/logs'):
    os.mkdir(f'{os.getcwd()}/logs')
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
    filename=f"{os.getcwd()}/logs/tfinance_main.log")
logger = logging.getLogger(__name__)


def send_stocks(update, start, end, templates):
    msg = ''
    for i in range(start, end):
        msg += templates['stocks'][i] + ', '
    update.message.reply_text(msg)


def get_list_stocks(update, context):
    try:
        templates = load_stocks('stocks.json')
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
    update.message.reply_text(f"Привет, {user.first_name}! Теперь доступ к командам открыт.")


def help(update, context):
    update.message.reply_text("/stocks [количество акций] Например: /stocks 100 - посмотреть первые 100 акций\n"
                              "/stocks all - посмотреть все акции на бирже\n"
                              "/stocks [буква алфавита] Например: /stocks A - посмотреть все акции, "
                              "название которых начинается с 'A'")


def favourites(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    stocks = Database('data.db').get_favourites_stocks(user)
    if stocks and stocks[0]:
        update.message.reply_text(', '.join(stocks[0].split()))
    else:
        update.message.reply_text('У вас нет избранных акций')


def follow(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    if context.args[0]:
        if Database('data.db').check_favourites_stocks(user, context.args[0]):
            update.message.reply_text('Акция уже в избранном')
        else:
            if check_stock(context.args[0].upper()):
                Database('data.db').add_favourites_stocks(user, context.args[0])
                update.message.reply_text('Акция добавлена в избранное')
            else:
                update.message.reply_text('Акция не найдена')


def unfollow(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    if context.args[0]:
        if not Database('data.db').check_favourites_stocks(user, context.args[0]):
            update.message.reply_text('Акции нет в избранном')
        else:
            Database('data.db').remove_favourites_stock(user.id, context.args[0])
            update.message.reply_text('Акция удалена из избранного')


def notify_assignees(context):
    db = Database('data.db')
    for user in db.get_users():
        if db.check_user_daily_notify(user.id):
            if user.favourites_stocks:
                for i in user.favourites_stocks.split():
                    try:
                        context.bot.send_photo(chat_id=user.id, photo=do_stock_image(i))
                    except Exception as e:
                        print(e)


def daily(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    Database('data.db').add_user(user)
    user_id = user.id
    if Database('data.db').check_user_daily_notify(user_id):
        update.message.reply_text(f'Ежедневная рассылка выключена')
    else:
        update.message.reply_text(f'Ежедневная рассылка включена')
    Database('data.db').user_daily_notify(user_id)


def stats(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    data = Database('data.db').read_info(user)
    try:
        update.message.reply_text(f'UserName: {data[0]}\nИзбранные акции:'
                                  f' {", ".join(data[1].split()) if data[1] else None}'
                                  f'\nОчки, заработанные в игре: {data[2]}')
    except TypeError:
        update.message.reply_text('Вас нет в бд, запустите команду /start чтобы исправить ошибку')


# Меню игры
def game_menu(update, context):
    try:
        if not context.args:
            update.message.reply_text("Неправильно введена команда! Попробуйте: /game [индекс акции]")
            return ConversationHandler.END

        user_data = update.effective_user
        user = User(user_data.to_dict())
        data = Database('data.db')
        message_id = str(int(update.message.message_id) + 2)

        if data.get_selected_stock(user, message_id):
            update.message.reply_text("Выполните прежний прогноз, чтобы начать новый! "
                                      "Чтобы отменить его нажмите выход.")
            return ConversationHandler.END

        data.select_stock(user, f"{context.args[0]}:{message_id}")

        if Database('data.db').check_prediction_stock(user, context.args[0]):
            update.message.reply_text("Прогноз на эту акцию уже установлен.")
            return ConversationHandler.END

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

    return 1


# Кнопка повышения акции
def higher_game(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    data = Database('data.db')

    query = update.callback_query
    query.answer()

    message_id = query.message.message_id
    data.add_prediction(user, data.get_selected_stock(user, message_id), 'up')
    data.remove_selected_stock(user, message_id)

    query.edit_message_text(text="Предсказание установлено на повышение")


# Кнопка понижения акции
def lower_game(update, context):
    user_data = update.effective_user
    user = User(user_data.to_dict())
    data = Database('data.db')

    query = update.callback_query
    query.answer()

    message_id = query.message.message_id
    data.add_prediction(user, data.get_selected_stock(user, message_id), 'down')
    data.remove_selected_stock(user, message_id)

    query.edit_message_text(text="Предсказание установлено на понижение")


# Подсчитывает результаты игры
def game_results(context):
    db = Database('data.db')
    for user in db.get_users():
        for i in user.prediction.split():

            # Проверяем прогноз
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

        # Удаляем пройденные прогнозы
        db.delete_predictions(user)
        user.prediction = db.get_predictions(user)


def main():
    # Создаём объект updater.
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue
    t = datetime.time(hour=20, minute=19, second=40, tzinfo=pytz.timezone('Europe/Moscow'))
    job_queue.run_daily(notify_assignees, t)
    job_queue.run_daily(game_results,
                        datetime.time(hour=3, tzinfo=pytz.timezone('Europe/Moscow')))

    conv_handler = ConversationHandler(entry_points=[CommandHandler("game", game_menu)],
                                       states={1: [CallbackQueryHandler(higher_game, pattern=f"^1$"),
                                                   CallbackQueryHandler(lower_game, pattern=f"^2$")]},
                                       fallbacks=[CommandHandler("game", game_menu)])
    dispatcher.add_handler(conv_handler)
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
