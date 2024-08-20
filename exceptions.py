class TokenNotAccessible(Exception):
    def __str__(self):
        return 'Токен недоступен!'


class UnexpectedResponseType(Exception):
    def __str__(self):
        return 'Некорректный ответ сервиса!'
    
class ExpectedResponseKeyNotFound(Exception):
    def __str__(self):
        return 'Некорректный ответ сервиса!'