import datetime
import pandas_datareader as pdr


def check_stock(stock_name):
    try:
        current_date = datetime.datetime.today()
        p_date = datetime.datetime.today() - datetime.timedelta(days=2)
        stock = pdr.get_data_yahoo(stock_name, start=p_date, end=current_date)
        return True
    except Exception as e:
        return False
