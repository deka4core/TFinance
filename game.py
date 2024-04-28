from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database import Database
from exceptions import EmptyDataFrameError, PredictionAlreadySet, StockSelectedAlready
from functions import create_user, generate_prediction, user_won
from graphics.visualize import check_stock_prices, do_stock_image
# Обработчик команды /game [stock_index]. Основное меню игры с предугадыванием.
from stock import check_stock


def game_menu(update, context):
    db: Database = Database()
    user = create_user(update)
    # Сохраняем id сообщения для возможности одновременной
    message_id = str(int(update.message.message_id) + 2)
    # Игры на многих акциях.
    # Прибавляем 2 т.к. отправляем 2 сообщения: фото и приписку к нему с клавиатурой.
    try:
        # Проверка на наличие аргументов.
        if not context.args:
            update.message.reply_text(
                "Неправильно введена команда! Попробуйте: /game [индекс акции]",
            )
        # Проверка: была ли выбрана акция до этого? Избегаем читерства.
        if db.check_selected_stocks(user):
            for stock in db.get_selected_stocks(user):
                if context.args[0] in stock:
                    raise StockSelectedAlready
        # Проверка: был ли прогноз на эту акцию.
        if db.check_prediction_stock(user, context.args[0]):
            raise PredictionAlreadySet
        if not check_stock(context.args[0]):
            raise KeyError

        # Создание клавиатуры и отправка ответа.
        keyboard = [[
            InlineKeyboardButton("Повышение", callback_data=str(1)),
            InlineKeyboardButton("Понижение", callback_data=str(2))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_photo(
            photo=do_stock_image(context.args[0]),
        )
        # Запоминаем, что акция была выбрана.
        db.select_stock(
            user, f"{context.args[0]}:{message_id}",
        )
        update.message.reply_text(
            text=f"Предугадайте курс {context.args[0]} на завтра.",
            reply_markup=reply_markup,
        )
    except EmptyDataFrameError:
        update.message.reply_text(
            "Такой акции не было найдено в данных Yahoo Finance.",
        )
        db.remove_selected_stock(user, message_id)
    except TypeError:
        update.message.reply_text(
            "Вас нет в бд, запустите команду /start чтобы исправить ошибку",
        )
    except KeyError:
        update.message.reply_text(
            text="Такой акции не было найдено в данных Yahoo Finance.",
        )
        db.remove_selected_stock(user, message_id)
    except StockSelectedAlready:
        update.message.reply_text(
            text="Эта акция уже была вами выбрана.",
        )
        db.remove_selected_stock(user, message_id)
    except PredictionAlreadySet:
        update.message.reply_text(
            text="Прогноз на эту акцию уже установлен.",
        )
        db.remove_selected_stock(user, message_id)

    # Возвращаем 1, чтобы показать ConversationHandler'у состояние, в котором находимся.
    return 1


# Кнопка повышения акции.
def higher_game(update, _):
    db: Database = Database()
    user = create_user(update)

    # Обработка и ответ на колл-бэк.
    query = update.callback_query
    query.answer()

    # Устанавливаем прогноз на акцию.
    generate_prediction(query, database=db, user=user, prediction="up")
    # Редактируем сообщение с клавиатурой.
    query.edit_message_text(text="Предсказание установлено на повышение")


# Кнопка понижения акции.
def lower_game(update, _):
    db: Database = Database()
    user = create_user(update)

    # Обработка и ответ на колл-бэк.
    query = update.callback_query
    query.answer()

    # Устанавливаем прогноз на акцию.
    generate_prediction(
        query, database=db, user=user, prediction="down",
    )
    # Редактируем сообщение с клавиатурой.
    query.edit_message_text(
        text="Предсказание установлено на понижение",
    )


# Подсчет результатов игры.
def game_results(context):
    db: Database = Database()
    for user in db.get_users():
        if not user.prediction:
            continue
        for i in user.prediction.split():
            # Проверка прогноза
            try:
                if i.split(":")[-1] == "up":
                    if check_stock_prices(i.split(":")[0]):
                        user_won(
                            context, database=db, user=user, stock=i.split(":")[0],
                        )
                    else:
                        context.bot.send_message(
                            chat_id=user.id,
                            text=f"Прогноз {i.split(':')[0]} был неверным.",
                        )
                else:
                    if not check_stock_prices(i.split(":")[0]):
                        user_won(
                            context, database=db, user=user, stock=i.split(":")[0],
                        )
                    else:
                        context.bot.send_message(
                            chat_id=user.id,
                            text=f"Прогноз {i.split(':')[0]} был неверным.",
                        )
            except KeyError:
                # Если биржа перестанет работать,
                # по непонятным нам причинам, то удалятся прошлые прогнозы.
                db.delete_predictions(user)
                context.bot.send_message(
                    chat_id=user.id,
                    text=f"На данный момент к бирже нет доступа."
                         f"Прогноз на акцию {i.split(':')[0]} был отменен.",
                )
        # Удаляем пройденные прогнозы
        db.delete_predictions(user)
        user.prediction = db.get_predictions(user)
