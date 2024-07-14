class User:
    def __init__(
        self,
        user_id: int,
        first_name: str,
        last_name: str,
        username: str,
        language_code: str,
        is_bot: bool,
        favourite_stocks=None,
        prediction=None,
        selected_stock=None,
    ):
        self.id: int = user_id
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.username: str = username
        self.language_code: str = language_code
        self.is_bot: bool = is_bot
        self.favourite_stocks = favourite_stocks
        self.prediction = prediction
        self.selected_stock = selected_stock
        self.points: int = 0
