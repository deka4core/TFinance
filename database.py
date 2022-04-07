import sqlite3

from items import User


class Database:
    def __init__(self, db_name):
        self.con = sqlite3.connect(db_name)
        self.cur = self.con.cursor()
        self.setup()

    def setup(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY ON CONFLICT IGNORE NOT NULL,
                first_name STRING, last_name STRING, username STRING, favourites_stocks STRING, points INTEGER);""")
        self.con.commit()

    def add_user(self, user: User):
        self.cur.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?);",
                         (user.id, user.first_name, user.last_name,
                          user.username, None, user.points))
        self.con.commit()

    def add_favourites_stocks(self, user: User, stock_name: str):
        stocks = self.cur.execute(f"SELECT favourites_stocks FROM users WHERE id = {user.id}").fetchone()
        if stocks and stocks[0]:
            stock_name = f'{stocks[0]} {stock_name}'
        self.cur.execute(f"UPDATE users SET favourites_stocks = '{stock_name}' WHERE id = {user.id}")
        self.con.commit()

    def check_favourites_stocks(self, user, stock_name: str):
        stocks = self.cur.execute(f"SELECT favourites_stocks FROM users WHERE id = {user.id}").fetchone()
        if stocks[0] and stock_name in stocks[0]:
            return True
        return False

    def get_favourites_stocks(self, user: User):
        stocks = self.cur.execute(f"SELECT favourites_stocks FROM users WHERE id = {user.id}").fetchone()
        return stocks
