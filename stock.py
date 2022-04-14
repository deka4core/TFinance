import json
import os
import datetime
import pandas_datareader as pdr
import requests

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0'}


def get_all_stocks():
    url = 'https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=6000&exchange=NASDAQ'
    stocks = requests.get(url, headers=HEADERS).json().get('data').get('table').get('rows')
    stocks = [i.get('symbol') for i in stocks]
    save_stocks('stocks.json', stocks)


def save_stocks(file_name, stocks: list):
    wd = os.getcwd()
    with open(f'{wd}/{file_name}', "w") as f:
        json.dump({'stocks': stocks}, f)


def load_stocks(file_name) -> list:
    wd = os.getcwd()
    if os.path.exists(f'{wd}/{file_name}'):
        with open(f'{wd}/{file_name}') as f:
            return json.load(f)
    return []


def check_stock(stock_name):
    try:
        current_date = datetime.datetime.today()
        p_date = datetime.datetime.today() - datetime.timedelta(days=2)
        stock = pdr.get_data_yahoo(stock_name, start=p_date, end=current_date)
        return True
    except Exception as e:
        return False
