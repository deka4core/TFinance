# Исключения для игры
class StockSelectedAlready(Exception):  # Акция уже выбрана
    pass


class PredictionAlreadySet(Exception):  # Прогноз на акцию уже установлен
    pass


# Исключения для графиков
class EmptyDataFrameError(Exception):  # Прогноз на акцию уже установлен
    pass
