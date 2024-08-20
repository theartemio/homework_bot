class TokenMissing(Exception):
    def __init__(self, missing_token):
        self.missing_token = missing_token

    def __str__(self):
        return f'Проблема с переменными окружения (токенами). Обязательная переменная {self.missing_token} не обнаружена!'

class ApiUnavailable(Exception):

    def __init__(self, response_code):
        self.response_code = response_code

    def __str__(self):
        return f'API сервиса Практикум.Домашка недоступен. Код ответа: {self.response_code}'
    
class ExpectedResponseKeyNotFound(Exception):
    
    def __init__(self, missing_key):
        self.missing_key = missing_key
    
    def __str__(self):
        return f'Некорректный ответ API. В ответе отсутствует ключ {self.missing_key}.'

class HomeworkNameNotFound(Exception):
    def __str__(self):
        return 'Отсутствует ключ Homework name!'
    



class UnexpectedResponseType(Exception):
    def __str__(self):
        return 'Некорректный ответ сервиса!'

class UnexpectedHomeworkStatus(Exception):
    def __str__(self):
        return 'Некорректный вердикт!'

