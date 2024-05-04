from telegram.ext import CallbackContext

from items import User


def create_user(update) -> User:
    return User(update.effective_user.to_dict())


# Установить прогноз акции
def generate_prediction(query, database, user: User, prediction: str):
    # Получаем id сообщения, для нахождения нужной сессии игры.
    message_id = query.message.message_id
    database.add_prediction(
        user, database.get_selected_stock_byid(user, message_id), prediction,
    )
    # Удаляем акцию из выбранных.
    database.remove_selected_stock(user, message_id)


# Сообщить о победе пользователя.
async def user_won(context: CallbackContext, database, user: User, stock: str):
    await context.bot.send_message(
        chat_id=user.id,
        text=f"""
Прогноз {stock} был верным.
Вы получили 1 очко.
Посмотреть кол-во очков можно, использовав /stats.
        """,
    )
    database.add_point(user)
