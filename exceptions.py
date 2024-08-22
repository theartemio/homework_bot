class TokenMissing(Exception):
    """Проблема с переменными окружения."""

    def __init__(self, missing_token):
        self.missing_token = missing_token

    def __str__(self):
        return f'''Проблема с переменными окружения (токенами).
        Обязательная переменная {self.missing_token} не обнаружена!
        Бот завершает работу'''


class ApiError(Exception):
    """Ошибка API сервиса Практикум.Домашка, либо ошибка в URL эндпоинта."""

    def __init__(self, response_code):
        self.response_code = response_code

    def __str__(self):
        return f'''Ошибка доступа к API сервиса.
        Проверьте код ответа эндпоинта. Код ответа: {self.response_code}'''


class ExpectedKeyNotFound(Exception):
    """В ответе отсутствует один из обязательных ключей."""

    def __init__(self, missing_key, item_name):
        self.missing_key = missing_key
        self.item_name = item_name

    def __str__(self):
        return f'''Получен некорректный {self.item_name}.
        В ответе отсутствует ключ {self.missing_key}.'''


class UnexpectedHomeworkStatus(Exception):
    """Статус работы не найден в словаре."""

    def __init__(self, verdict):
        self.verdict = verdict
    def __str__(self):
        return f'Некорректный вердикт! Получен вердикт {self.verdict}'
