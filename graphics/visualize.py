import io

import matplotlib.pyplot as plt
import yfinance as yf

from exceptions import EmptyDataFrameError, WrongPeriodError

time_periods = {
    "1d": "за 1 день",
    "5d": "за 5 дней",
    "1mo": "за 1 месяц",
    "3mo": "за 3 месяца",
    "6mo": "за 6 месяцев",
    "1y": "за 1 год",
    "2y": "за 2 года",
    "5y": "за 5 лет",
    "10y": "за 10 лет",
    "ytd": "с начала года",
    "max": "за всё время",
}


def do_stock_image(stock_name, period="1mo"):
    """
        Создание графика акции.
    :param stock_name: Строка, содержащая индекс названия акции.
    :param period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    :return: Картинка в байтовом формате.
    """
    if period not in time_periods:
        raise WrongPeriodError
    # Забираем данные из Yahoo Finance.
    stock = yf.download(stock_name, period=period)
    if stock.empty:
        raise EmptyDataFrameError
    # Очищаем полотно от прошлых графов.
    plt.clf()

    # Создаем полотно с графиком.
    stock["Close"].plot(grid=True)
    plt.title(f"Курс акции {stock_name} {time_periods.get(period)}", fontsize=14)
    plt.gca().set(ylabel="Price USD")

    # Записываем полученный график в байты и возвращаем полученное изображение.
    output = io.BytesIO()
    plt.savefig(output)
    return output.getvalue()


def check_stock_prices(stock_name) -> bool:
    """
        Получить информацию об изменении курса акции.
    :param stock_name: Строка, содержащая индекс названия акции.
    :return: Булево значение в результате сравнения цен.
    """
    stock = yf.download(stock_name, period="5d")

    # Цены за последние 2 дня
    prev_price = stock["Close"][-2]
    curr_price = stock["Close"][-1]

    return curr_price > prev_price
