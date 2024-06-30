# Ежедневная рассылка избранных акций.
import logging

from telegram import Update
from telegram.ext import CallbackContext

from database import Database
from functions import create_user
from graphics.visualize import do_stock_image


async def notify_assignees(context: CallbackContext):
    db = Database()
    # Перебираем всех пользователей и рассылаем каждому курсы их избранных акций.
    for user in db.get_users():
        if db.check_user_daily_notify(user):
            if user.favourite_stocks:
                for i in user.favourite_stocks.split():
                    try:
                        await context.bot.send_photo(
                            chat_id=user.id,
                            photo=do_stock_image(i),
                        )
                    except Exception as e:
                        logging.exception(e)


# Включение/выключение ежедневной рассылки.
async def daily(update: Update, _):
    db = Database()
    user = create_user(update)
    db.add_user(user)
    if db.check_user_daily_notify(user):
        await update.message.reply_text("Ежедневная рассылка выключена")
    else:
        await update.message.reply_text("Ежедневная рассылка включена")
    db.user_daily_notify(user)
