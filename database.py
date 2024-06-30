import sqlite3

from models import User


def singleton(cls):
    instance = [None]

    def wrapper(*args, **kwargs):
        if instance[0] is None:
            instance[0] = cls(*args, **kwargs)
        return instance[0]

    return wrapper


@singleton
class Database:
    """
    Класс БД с данными о пользователях.
    """

    def __init__(self):
        # Подключение к БД с отключенной проверкой потока.
        self.con = sqlite3.connect("data.db", check_same_thread=False)
        self.cur = self.con.cursor()
        self.setup()

    def setup(self):
        """
            Настройка БД, если она еще не была создана.
        :return: None
        """
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY ON CONFLICT IGNORE NOT NULL,
            first_name STRING,
            last_name STRING,
            username STRING,
            language_code STRING,
            is_bot BOOLEAN,
            favourites_stocks STRING,
            prediction STRING,
            selected_stock STRING,
            points INTEGER,
            daily_notify BOOLEAN
            );
            """,
        )
        self.con.commit()

    def add_user(self, user: User):
        """
            Добавить пользователя в БД.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :return: None
        """
        self.cur.execute(
            "INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (
                user.id,
                user.first_name,
                user.last_name,
                user.username,
                user.language_code,
                user.is_bot,
                None,
                None,
                None,
                user.points,
                False,
            ),
        )
        self.con.commit()

    def get_users(self) -> list[User]:
        """
            Получить список пользователей.
        :return: Возвращает список всех пользователей, записанных в БД.
        """
        users = self.cur.execute(
            "SELECT * FROM users",
        ).fetchall()
        return [
            User(
                user_id=row[0],
                first_name=row[1],
                last_name=row[2],
                username=row[3],
                language_code=row[4],
                is_bot=bool(row[5]),
                favourite_stocks=row[6],
                prediction=row[7],
                selected_stock=row[8],
            )
            for row in users
        ]

    def add_prediction(self, user: User, stock_name: str, updown: str):
        """
            Добавить прогноз пользователю в БД.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :param stock_name: Строка, содержащая индекс названия акции.
        :param updown: Тип прогноза (выше, ниже).
        :return: None
        """
        predictions = self.cur.execute(
            f"SELECT prediction FROM users WHERE id = {user.id}",
        ).fetchone()
        prediction = f"{stock_name}:{updown}"
        if predictions[0]:
            prediction = f"{predictions[0]} {prediction}"
        self.cur.execute(
            f"UPDATE users SET prediction = ' {prediction}' WHERE id = {user.id}",
        )
        self.con.commit()

    def check_prediction_stock(self, user: User, stock_name: str) -> bool:
        """
            Проверка на наличие акции в списке прогнозов.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :param stock_name: Строка, содержащая индекс названия акции.
        :return: Булево значение результата проверки.
        """
        stocks = self.cur.execute(
            f"SELECT prediction FROM users WHERE id = {user.id}",
        ).fetchone()
        if stocks[0] and stock_name in stocks[0]:
            return True
        return False

    def get_predictions(self, user: User) -> str:
        """
            Получить список всех прогнозов пользователя.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :return: Информация о прогнозах пользователя в виде строки.
        """
        return self.cur.execute(
            f"SELECT prediction FROM users WHERE id = {user.id}",
        ).fetchone()[0]

    def delete_predictions(self, user: User):
        """
            Удалить все прогнозы у пользователя.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :return: None
        """
        self.cur.execute(f"UPDATE users SET prediction = '' WHERE id = {user.id}")
        self.con.commit()

    def select_stock(self, user: User, stock_name: str):
        """
            Выбрать акцию.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :param stock_name: Строка, содержащая индекс названия акции.
        :return: None
        """
        selected_stocks = self.cur.execute(
            f"SELECT selected_stock FROM users WHERE id = {user.id}",
        ).fetchone()[0]
        if selected_stocks:
            stock_name = f"{selected_stocks} {stock_name}"
        self.cur.execute(
            f"UPDATE users SET selected_stock = '{stock_name}' WHERE id = {user.id}",
        )
        self.con.commit()

    def get_selected_stock_byid(self, user: User, message_id) -> str:
        """
            Получить название акции по id сообщения с игрой.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :param message_id: ID сообщения с игрой.
        :return: Название акции в виде строки (str)
        """
        data = self.cur.execute(
            f"SELECT selected_stock FROM users WHERE id = {user.id}",
        ).fetchone()[0]
        if data:
            for i in data.split():
                if str(message_id) == i.split(":")[-1]:
                    return i.split(":")[0]

    def get_selected_stocks(self, user: User) -> list:
        """
            Получить все выбранные акции.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :return: Список выбранных акций (list)
        """
        data = self.cur.execute(
            f"SELECT selected_stock FROM users WHERE id = {user.id}",
        ).fetchone()[0]
        return data.split()

    def check_selected_stocks(self, user: User) -> bool:
        """
            Проверить, есть ли выбранные акции у пользователя.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :return: Булево значение с результатом проверки
        """
        stocks = self.cur.execute(
            f"SELECT selected_stock FROM users WHERE id = {user.id}",
        ).fetchone()[0]
        if stocks:
            return True
        return False

    def remove_selected_stock(self, user: User, msg_id: str):
        """
            Удалить выбранную акцию, используя id сообщения с игрой
        :param user: Экземпляр класса User с данными об этом пользователе.
        :param msg_id: ID сообщения с игрой.
        :return: None
        """
        selected_stocks = (
            self.cur.execute(
                f"SELECT selected_stock FROM users WHERE id = {user.id}",
            )
            .fetchone()[0]
            .split()
        )
        for i in range(len(selected_stocks)):
            if str(msg_id) == selected_stocks[i].split(":")[-1]:
                del selected_stocks[i]
                break
        selected_stocks = " ".join(selected_stocks)
        self.cur.execute(
            f"""UPDATE users SET selected_stock = '{selected_stocks}'
            WHERE id = {user.id}""",
        )
        self.con.commit()

    def read_info(self, user: User) -> tuple:
        """
            Получить информацию для статистки пользователя.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :return: Информация о пользователе.
        """
        return self.cur.execute(
            f"SELECT username, favourites_stocks,"
            f"points FROM users WHERE id = {user.id}",
        ).fetchone()

    def add_favourites_stocks(self, user: User, stock_name: str):
        """
            Добавление акции в избранные.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :param stock_name: Строка, содержащая индекс названия акции.
        :return: None
        """
        stocks = self.cur.execute(
            f"SELECT favourites_stocks FROM users WHERE id = {user.id}",
        ).fetchone()
        if stocks and stocks[0]:
            stock_name = f"{stocks[0]} {stock_name}"
        self.cur.execute(
            f"UPDATE users SET favourites_stocks = '{stock_name}' WHERE id = {user.id}",
        )
        self.con.commit()

    def check_favourites_stocks(self, user: User, stock_name: str) -> bool:
        """
            Проверка на наличие акции в избранных.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :param stock_name: Строка, содержащая индекс названия акции.
        :return: Булево значение результата проверки.
        """
        stocks = self.cur.execute(
            f"SELECT favourites_stocks FROM users WHERE id = {user.id}",
        ).fetchone()
        if stocks[0] and stock_name in stocks[0].split():
            return True
        return False

    def get_favourites_stocks(self, user: User) -> tuple:
        """
            Получить список избранных акций.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :return: Список избранных акций (tuple)
        """
        return self.cur.execute(
            f"SELECT favourites_stocks FROM users WHERE id = {user.id}",
        ).fetchone()

    def remove_favourites_stock(self, user: User, stock_name: str):
        """
            Удалить избранную акцию.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :param stock_name: Строка, содержащая индекс названия акции.
        :return: None
        """
        stocks = self.cur.execute(
            f"SELECT favourites_stocks FROM users WHERE id = {user.id}",
        ).fetchone()
        if stocks[0]:
            a = stocks[0].split()
            a.remove(stock_name)
            if not a:
                a = "null"
            else:
                a = f"'{' '.join(a)}'"
            self.cur.execute(
                f"UPDATE users SET favourites_stocks = {a} WHERE id = {user.id}",
            )
            self.con.commit()

    def user_daily_notify(self, user: User):
        """
            Изменить значение ежедневной рассылки.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :return: None
        """
        self.cur.execute(
            f"UPDATE users SET daily_notify = NOT daily_notify WHERE id = {user.id}",
        )
        self.con.commit()

    def check_user_daily_notify(self, user: User) -> bool:
        """
            Проверить наличие ежедневной рассылки.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :return: Булево значение результата проверки
        """
        a = self.cur.execute(
            f"SELECT daily_notify FROM users WHERE id = {user.id}",
        ).fetchone()
        return bool(a[0])

    def add_point(self, user: User):
        """
            Добавить очко пользователю.
        :param user: Экземпляр класса User с данными об этом пользователе.
        :return: None
        """
        prev_num = self.cur.execute(
            f"SELECT points FROM users WHERE id = {user.id}",
        ).fetchone()[0]
        self.cur.execute(
            f"UPDATE users SET points = {prev_num + 1} WHERE id = {user.id}",
        )
        user.points += 1
        self.con.commit()
