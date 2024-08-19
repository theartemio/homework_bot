import requests

from pprint import pprint
import os
import requests

from dotenv import load_dotenv
from telebot import TeleBot, types
import logging


load_dotenv()

url = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
headers = {'Authorization': 'OAuth y0_AgAAAAArhdq1AAYckQAAAAENrU0tAACVeQgjlUJKpofdXYW1klOIBrEj9g'}
payload = {'from_date': 1549962000}

# Делаем GET-запрос к эндпоинту url с заголовком headers и параметрами params


# Печатаем ответ API в формате JSON
# print(homework_statuses.text)

# А можно ответ в формате JSON привести к типам данных Python и напечатать и его
pprint(homework_statuses.json())






PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}



class TokenNotFoundException(Exception):
    pass                                  

'''
def check_tokens(practicum_token, telegram_token, telegram_chat_id):
        tokens = (
            ('practicum_token', practicum_token),
            ('telegram_token', telegram_token), 
            ('telegram_chat_id', telegram_chat_id),
        )
        
        for token_name, token_value  in tokens:
            try:
                token_value
                continue
            else:
                raise TokenNotFoundException as error:
                    message = f'Ошибка токена {error}. Отсутствует токен {missing_token}'
'''

def send_message(bot, message):
    '''
    Отправляет сообщение в Telegram-чат, определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра: экземпляр класса TeleBot и строку с текстом сообщения.
    '''
    chat_id = message.chat.id
    name = message.from_user.first_name
    # keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # button = types.KeyboardButton('/newcat')
    # keyboard.add(button)
    bot.send_message(
        chat_id=chat_id,
        text=f'Привет, {name}. ',
        reply_markup=keyboard,
    )


def get_api_answer(timestamp):
    homework_statuses = requests.get(url, headers=HEADERS, params=payload)
    homework = homework_statuses[1]
    return homework


def check_response(response):
    '''
    Проверяет  ответ API на соответствие документации из урока «API сервиса Практикум Домашка».
    В качестве параметра функция получает ответ API, приведённый к типам данных Python.
    '''
    ...


def parse_status(homework_list):
    '''
    Извлекает из информации о конкретной домашней работе статус этой работы. 
    В качестве параметра функция получает только один элемент из списка домашних работ. 
    В случае успеха функция возвращает подготовленную для отправки в Telegram строку, 
    содержащую один из вердиктов словаря HOMEWORK_VERDICTS.
    '''
    request_date = ...
    for homework in homework_list:
        if request_date > homework['date_updated']:
            homework_name = homework['homework_name']
            verdict = HOMEWORK_VERDICTS[homework['verdict']]
            return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            
        ...


if __name__ == '__main__':
    main()
