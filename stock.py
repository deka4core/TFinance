import datetime
import json
import os

import pandas.core.frame
import pandas_datareader as pdr


def get_stock(name) -> pandas.core.frame.DataFrame:
    current_date = datetime.datetime.today()
    yesterday = current_date - datetime.timedelta(days=1)
    stock = pdr.get_data_yahoo(name, start=yesterday, end=current_date)
    return stock


def load_stocks(file_name) -> dict:
    wd = os.getcwd()
    if os.path.exists(f'{wd}/{file_name}'):
        with open(f'{wd}/{file_name}') as f:
            return json.load(f)
    return {}
