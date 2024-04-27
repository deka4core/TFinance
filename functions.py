from items import User


# Исключения для игры
class StockSelectedAlready(Exception):  # Акция уже выбрана
    pass


class PredictionAlreadySet(Exception):  # Прогноз на акцию уже установлен
    pass


# Создать экземпляр класса User
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
def user_won(context, database, user: User, stock: str):
    context.bot.send_message(chat_id=user.id, text=f"Прогноз {stock} был верным. "
                                                   f"\nВы получили 1 очко. "
                                                   f"\nПосмотреть кол-во очков можно, "
                                                   f"использовав /stats.")
    database.add_point(user)
