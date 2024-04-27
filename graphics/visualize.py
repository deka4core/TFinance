import io
import yfinance as yf
import matplotlib.pyplot as plt


def do_stock_image(stock_name):
    """
        Создание графика акции.
    :param stock_name: Строка, содержащая индекс названия акции.
    :return: Картинка в байтовом формате.
    """

    # Забираем данные из Yahoo Finance.
    stock = yf.download(stock_name, period="1mo")

    # Очищаем полотно от прошлых графов.
    plt.clf()

    # Создаем полотно с графиком.
    stock["Close"].plot(grid=True)
    plt.title(f"Курс акции {stock_name} за последние 30 дней", fontsize=14)
    plt.gca().set(ylabel="Price")

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
