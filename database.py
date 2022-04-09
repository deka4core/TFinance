import sqlite3

from items import User


class Database:
    def __init__(self, db_name):
        self.con = sqlite3.connect(db_name)
        self.cur = self.con.cursor()
        self.setup()

    def setup(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY ON CONFLICT IGNORE NOT NULL, 
        first_name STRING, last_name STRING, username STRING, favourites_stocks STRING, prediction STRING,
        selected_stock STRING, points INTEGER, daily_notify BOOLEAN);""")
        self.con.commit()

    def add_user(self, user: User):
        self.cur.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);",
                         (user.id, user.first_name, user.last_name,
                          user.username, None, None, None, user.points, False))
        self.con.commit()

    def get_users(self):
        users = self.cur.execute(f"SELECT * FROM users").fetchall()
        return [User({'id': i[0], 'chat_id': i[1], 'first_name': i[2], 'last_name': i[3], 'username': i[4],
                      'favourites_stocks': i[5], 'prediction': i[6], 'selected_stock': i[7],
                      'points': i[8]}) for i in users]

    def add_prediction(self, user: User, stock_name: str, updown: str):
        predictions = self.cur.execute(f"SELECT prediction FROM users WHERE id = {user.id}").fetchone()
        prediction = f"{stock_name}:{updown}"
        if predictions[0]:
            prediction = f'{predictions[0]} {prediction}'
        self.cur.execute(f"UPDATE users SET prediction = ' {prediction}' WHERE id = {user.id}")
        self.con.commit()

    def check_prediction_stock(self, user: User, stock_name: str):
        stocks = self.cur.execute(f"SELECT prediction FROM users WHERE id = {user.id}").fetchone()
        if stocks[0] and stock_name in stocks[0]:
            return True
        return False

    def get_predictions(self, user: User):
        data = self.cur.execute(
            f"SELECT prediction FROM users WHERE id = {user.id}").fetchone()[0]
        return data

    def delete_predictions(self, user: User):
        self.cur.execute(f"UPDATE users SET prediction = '' WHERE id = {user.id}")
        self.con.commit()

    def select_stock(self, user: User, stock_name: str):
        self.cur.execute(f"UPDATE users SET selected_stock = '{stock_name}' WHERE id = {user.id}")
        self.con.commit()

    def get_selected_stock(self, user) -> str:
        data = self.cur.execute(
            f"SELECT selected_stock FROM users WHERE id = {user.id}").fetchone()[0]
        return data

    def read_info(self, user):
        data = self.cur.execute(f"SELECT username, favourites_stocks, points FROM users WHERE id = {user.id}").fetchone()
        return data

    def add_favourites_stocks(self, user: User, stock_name: str):
        stocks = self.cur.execute(f"SELECT favourites_stocks FROM users WHERE id = {user.id}").fetchone()
        if stocks and stocks[0]:
            stock_name = f'{stocks[0]} {stock_name}'
        self.cur.execute(f"UPDATE users SET favourites_stocks = '{stock_name}' WHERE id = {user.id}")
        self.con.commit()

    def check_favourites_stocks(self, user, stock_name: str):
        stocks = self.cur.execute(f"SELECT favourites_stocks FROM users WHERE id = {user.id}").fetchone()
        if stocks[0] and stock_name in stocks[0].split():
            return True
        return False

    def get_favourites_stocks(self, user: User):
        stocks = self.cur.execute(f"SELECT favourites_stocks FROM users WHERE id = {user.id}").fetchone()
        return stocks

    def remove_favourites_stock(self, user_id, stock_name: str):
        stocks = self.cur.execute(f"SELECT favourites_stocks FROM users WHERE id = {user_id}").fetchone()
        if stocks[0]:
            print(stocks[0])
            a = stocks[0].split()
            a.remove(stock_name)
            if not a:
                a = 'null'
            else:
                a = f"'{' '.join(a)}'"
            self.cur.execute(f"UPDATE users SET favourites_stocks = {a} WHERE id = {user_id}")
            self.con.commit()

    def user_daily_notify(self, user_id: int):
        self.cur.execute(f"UPDATE users SET daily_notify = NOT daily_notify WHERE id = {user_id}")
        self.con.commit()

    def check_user_daily_notify(self, user_id: int) -> bool:
        a = self.cur.execute(f"SELECT daily_notify FROM users WHERE id = {user_id}").fetchone()
        return bool(a[0])

    def add_point(self, user: User):
        prev_num = self.cur.execute(
            f"SELECT points FROM users WHERE id = {user.id}").fetchone()[0]
        self.cur.execute(f"UPDATE users SET points = {prev_num + 1} WHERE id = {user.id}")
        user.points += 1
        self.con.commit()
