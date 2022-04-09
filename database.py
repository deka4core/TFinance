import sqlite3

from items import User


class Database:
    def __init__(self, db_name):
        self.con = sqlite3.connect(db_name)
        self.cur = self.con.cursor()
        self.setup()

    def setup(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY ON CONFLICT IGNORE NOT NULL,
         first_name STRING, last_name STRING, username STRING, favourites_stocks STRING, points INTEGER,
         daily_notify BOOLEAN);""")
        self.con.commit()

    def add_user(self, user: User):
        self.cur.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?);",
                         (user.id, user.first_name, user.last_name,
                          user.username, None, user.points, False))
        self.con.commit()

    def get_users(self):
        users = self.cur.execute(f"SELECT * FROM users").fetchall()
        return [User({'id': i[0], 'first_name': i[1], 'last_name': i[2], 'username': i[3],
                      'favourites_stocks': i[4], 'points': i[5]}) for i in users]

    def add_favourites_stocks(self, user: User, stock_name: str):
        stocks = self.cur.execute(f"SELECT favourites_stocks FROM users WHERE id = {user.id}").fetchone()
        if stocks and stocks[0]:
            stock_name = f'{stocks[0]} {stock_name}'
        self.cur.execute(f"UPDATE users SET favourites_stocks = '{stock_name}' WHERE id = {user.id}")
        self.con.commit()

    def read_info(self, user):
        data = self.cur.execute(f"SELECT username, favourites_stocks, points FROM users WHERE id = {user.id}").fetchone()
        return data

    def check_favourites_stocks(self, user, stock_name: str):
        stocks = self.cur.execute(f"SELECT favourites_stocks FROM users WHERE id = {user.id}").fetchone()
        if stocks[0] and stock_name in stocks[0].split():
            return True
        return False

    def get_favourites_stocks(self, user: User):
        stocks = self.cur.execute(f"SELECT favourites_stocks FROM users WHERE id = {user.id}").fetchone()
        return stocks

    def user_daily_notify(self, user_id: int):
        self.cur.execute(f"UPDATE users SET daily_notify = NOT daily_notify WHERE id = {user_id}")
        self.con.commit()

    def check_user_daily_notify(self, user_id: int) -> bool:
        a = self.cur.execute(f"SELECT daily_notify FROM users WHERE id = {user_id}").fetchone()
        return bool(a[0])

