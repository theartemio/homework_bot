class TokenMissing(Exception):
    """Проблема с переменными окружения."""

    def __init__(self, missing_tokens_names):
        self.missing_tokens_names = missing_tokens_names

    def __str__(self):
        return f'''Проблема с переменными окружения (токенами).
        Обязательная переменная {self.missing_tokens_names} не обнаружена!
        Бот завершает работу'''


class ApiError(Exception):
    """Ошибка API сервиса Практикум.Домашка, либо ошибка в URL эндпоинта."""

    def __init__(self, response_code, response_name):
        self.response_code = response_code
        self.response_name = response_name

    def __str__(self):
        return f'''Ошибка доступа к API сервиса.
        Код ответа: {self.response_code}, описаниа: {self.response_name}'''


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
    
class RequestError(Exception):
    """Ошибка запроса."""

    def __init__(self, error):
        self.error = error

    def __str__(self):
        return f'При запросе возникла ошибка {self.error}'

