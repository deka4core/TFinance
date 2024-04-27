# Ежедневная рассылка избранных акций.
import logging

from database import Database
from functions import create_user
from graphics.visualize import do_stock_image


def notify_assignees(context):
    db = Database("data.db")
    # Перебираем всех пользователей и рассылаем каждому курсы их избранных акций.
    for user in db.get_users():
        if db.check_user_daily_notify(user):
            if user.favourites_stocks:
                for i in user.favourites_stocks.split():
                    try:
                        context.bot.send_photo(chat_id=user.id, photo=do_stock_image(i))
                    except Exception as e:
                        logging.exception(e)


# Включение/выключение ежедневной рассылки.
def daily(update, _):
    db = Database("data.db")
    user = create_user(update)
    db.add_user(user)
    if db.check_user_daily_notify(user):
        update.message.reply_text("Ежедневная рассылка выключена")
    else:
        update.message.reply_text("Ежедневная рассылка включена")
    db.user_daily_notify(user)
