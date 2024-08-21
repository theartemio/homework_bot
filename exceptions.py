class TokenMissing(Exception):
    def __init__(self, missing_token):
        self.missing_token = missing_token

    def __str__(self):
        return f'Проблема с переменными окружения (токенами). Обязательная переменная {self.missing_token} не обнаружена! Бот завершает работу'

class ApiUnavailable(Exception):

    def __init__(self, response_code):
        self.response_code = response_code

    def __str__(self):
        return f'API сервиса Практикум.Домашка недоступен. Код ответа: {self.response_code}'
    
class ExpectedKeyNotFoundTwo(Exception):
    
    def __init__(self, missing_key, item_name):
        self.missing_key = missing_key
        self.item_name = item_name
    
    def __str__(self):
        return f'Получен некорректный {self.item_name}. В ответе отсутствует ключ {self.missing_key}.'

class ExpectedKeyNotFound(Exception):
    
    def __init__(self, missing_key, item_name):
        self.missing_key = missing_key
    
    def __str__(self):
        return f'Получен некорректный ответ. В ответе отсутствует ключ {self.missing_key}.'

class HomeworkNameNotFound(Exception):
    def __str__(self):
        return 'Отсутствует ключ Homework name!'
    

class UnexpectedResponseType(Exception):
    def __str__(self):
        return 'Некорректный ответ сервиса!'

class UnexpectedHomeworkStatus(Exception):
    
    def __init__(self, verdict):
        self.verdict = verdict
    def __str__(self):
        return f'Некорректный вердикт! Получен вердикт {self.verdict}'

