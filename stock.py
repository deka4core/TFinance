import datetime
import json
import os

import pandas_datareader as pdr


def get_stock(name):
    current_date = datetime.datetime.today()
    stock = pdr.get_data_yahoo(name, current_date)
    return stock


def load_stocks(file_name):
    wd = os.getcwd()
    if os.path.exists(f'{wd}/{file_name}'):
        with open(f'{wd}/{file_name}') as f:
            return json.load(f)
    return {}
