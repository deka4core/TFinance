import json
import logging
from pathlib import Path

import requests
import yfinance as yf


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) "
    "Gecko/20100101 Firefox/99.0",
}


# Загрузка списка всех акций.
def load_stocks(file_name: str) -> list[dict[str, str]]:
    path = Path(f"{Path.cwd()}/{file_name}")
    if path.exists():
        with path.open() as f:
            return json.load(f)
    return []


# Проверка на существование акции.
def check_stock(stock_name: str) -> bool:
    try:
        stock = yf.download(stock_name, period="1mo")
        if stock["Close"][-2]:
            return True
    except Exception as e:
        logging.exception(e)
        return False


# Сохранение списка акций в json.
def save_stocks(file_name: str, stocks: list):
    with Path(f"{Path.cwd()}/{file_name}").open("w") as f:
        json.dump(stocks, f)


# Получение списка акций и их сохранение.
def get_all_stocks():
    url = (
        "https://api.nasdaq.com/api/screener/stocks?"
        "tableonly=true&limit=6000&exchange=NASDAQ"
    )
    stocks = (
        requests.get(
            url,
            headers=HEADERS,
        )
        .json()
        .get("data")
        .get("table")
        .get("rows")
    )
    stocks = [{"symbol": i.get("symbol"), "name": i.get("name")} for i in stocks]
    save_stocks("stocks.json", stocks)
