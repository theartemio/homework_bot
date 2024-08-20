

from pprint import pprint
import os
import requests
import time
from dotenv import load_dotenv

from telebot import TeleBot, types
import logging

from exceptions import TokenNotAccessible, UnexpectedResponseType, ExpectedResponseKeyNotFound


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename='homework_bot.log',
    filemode='a'
)


def check_tokens():
    '''
    Функция проверяет существование обязательных переменных окружения:
    PRACTICUM_TOKEN
    TELEGRAM_TOKEN
    TELEGRAM_CHAT_ID
    '''
    tokens = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
              'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
              'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
              }
    for token in tokens:
        if not tokens[token]:
            token_error_message = f'''Отсутствует обязательная переменная
            окружения {token} во время запуска бота'''
            logging.critical(token_error_message) 
            raise TokenNotAccessible

def send_message(bot, message):
    '''
    Отправляет сообщение в Telegram-чат, определяемый переменной окружения
    TELEGRAM_CHAT_ID.
    Принимает на вход два параметра:
    bot - экземпляр класса TeleBot
    message - строку с текстом сообщения.
    '''
    chat_id = TELEGRAM_CHAT_ID
    try:
        bot.send_message(chat_id=chat_id, text=message)
        logging.debug(f'''Удачная отправка сообщения в Telegram.
                      Отправлено сообщение: {message}''')
    except Exception as error:
        logging.error(f'Ошибка {error}')


def get_api_answer(timestamp):
    '''Получает ответ, содержащий список домашек с изменившимся статусом
    на момент от timestamp до настоящего времени. Принимает аргументы:
    timestamp - временную метку
    '''
    try:
        homework_statuses = requests.get(url=ENDPOINT, headers=HEADERS, params=timestamp)
    except Exception as error:
        logging.error(f'Недоступен эндпоинт {ENDPOINT}. Ошибка: {error}')
    homework_statuses_json = homework_statuses.json()
    return homework_statuses_json


def check_response(response):
    '''Проверяет ответ API на соответствие документации API сервиса Практикум Домашка.
    В качестве параметра функция получает:
    response - ответ API, приведённый к типам данных Python.'''
    reponse_type = type(response)
    response_expected_keys =('homeworks', 'current_date')
    if reponse_type != dict:
        logging.error(f'Некорректный ответ API. Ожидался dict, получен {reponse_type}.')
        raise UnexpectedResponseType
    for key in response_expected_keys:
        if key not in response.keys():
            logging.error(f'Некорректный ответ API. В ответе отсутствует ключ {key}.')
            raise ExpectedResponseKeyNotFound


def parse_status(homework):
    '''
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка домашних работ.
    В случае успеха функция возвращает подготовленную для отправки в Telegram строку,
    содержащую один из вердиктов словаря HOMEWORK_VERDICTS
    '''
    homework_name = homework['homework_name']
    try:
        verdict = HOMEWORK_VERDICTS[homework['status']]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        logging.error(f'Неожиданный статус домашней работы, обнаруженный в ответе API. Ошибка: {error}')    


def main():
    '''
    Основная логика работы бота.

    '''
    bot = TeleBot(token=TELEGRAM_TOKEN)
    # timestamp = int(time.time())
    timestamp = 0
    while True:
        try:
            check_tokens()
            status = f'Проверяю период от {timestamp} до {int(time.time())}'
            send_message(bot, status)
            payload = {'from_date': timestamp}
            homeworks = get_api_answer(payload)
            pprint(homeworks)
            check_response(homeworks)
            homeworks_list = homeworks['homeworks']
            if not homeworks_list:
                logging.debug(f'Отсутствие в ответе новых статусов.')
                send_message(bot, 'Обновлений нет')
            for homework in homeworks:
                status_update = parse_status(homework)
                send_message(bot, status_update)
            timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)
        except UnexpectedResponseType or ExpectedResponseKeyNotFound as error:
            continue
        except TokenNotAccessible as error:
            logging.critical(f'Отсутствует переменная окружения, ошибка {error}')
            break
        except Exception as error:
            message = f'Сбой в работе программы: {error}'


if __name__ == '__main__':
    main()
