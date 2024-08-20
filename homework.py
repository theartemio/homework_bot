
import os
import requests
import time
from dotenv import load_dotenv

from telebot import TeleBot, types
import logging

from exceptions import (
    TokenMissing,
    UnexpectedResponseType,
    ExpectedResponseKeyNotFound,
    UnexpectedHomeworkStatus,
    ApiUnavailable,
    HomeworkNameNotFound,
)


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# RETRY_PERIOD = 15
RETRY_PERIOD = 600
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
            raise TokenMissing(token)

def send_message(bot, message):
    '''
    Отправляет сообщение в Telegram-чат, определяемый переменной окружения
    TELEGRAM_CHAT_ID.
    Принимает два параметра:
    bot - экземпляр класса TeleBot
    message - строку с текстом сообщения
    '''
    chat_id = TELEGRAM_CHAT_ID
    try:
        bot.send_message(chat_id=chat_id, text=message)
        logging.debug(f' Успешно отправлено сообщение: {message}')
    except Exception as error:
        logging.error(f'Сообщение {message} не отправлено. Ошибка: {error}')


def get_api_answer(timestamp):
    '''
    Получает ответ, содержащий список домашек, статус которых поменялся в период
    от timestamp до настоящего времени. Принимает аргументы:
    timestamp - временную метку в формате Unix-времени
    '''
    try:
        homework_statuses = requests.get(url=ENDPOINT, headers=HEADERS, params=timestamp)
        if homework_statuses.status_code != 200:
            raise ApiUnavailable(homework_statuses.status_code)
        homework_statuses_json = homework_statuses.json()
        return homework_statuses_json
    except requests.RequestException:
        pass




def check_response(response):
    '''Проверяет ответ на соответствие документации API сервиса Практикум.Домашка.
    В качестве параметра функция получает:
    response - ответ API, приведённый к типам данных Python.'''
    
    reponse_type = type(response)
    expected_type = dict
    response_keys_and_types = {'homeworks': list, 
                               'current_date': int,}
    if not isinstance(response, expected_type):
        raise TypeError(f'Некорректный ответ API. Ожидался {expected_type.__name__}, получен {reponse_type.__name__}.')
    logging.debug(f'Ответ API проверен. Тип ответа: {reponse_type} соответствует ожидаемому.')
    for key, value in response_keys_and_types.items():
        if key not in response.keys():
            raise ExpectedResponseKeyNotFound(key)
        if not isinstance(response[key], value):
            raise TypeError(f'Некорректный ответ API. Ожидался тип значения {key} равный {value}, получен {type(response[key])}')
    logging.debug(f'API response checked. All expected keys found')






def parse_status(homework):
    '''
    Извлекает из словаря с информацией о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка домашних работ.
    В случае успеха функция возвращает подготовленную для отправки в Telegram строку,
    содержащую один из вердиктов словаря HOMEWORK_VERDICTS
    '''
    if 'homework_name' not in homework.keys():
        raise HomeworkNameNotFound
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status in HOMEWORK_VERDICTS.keys():
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        raise UnexpectedHomeworkStatus


def main():
    '''
    Основная логика работы бота.
    '''
    bot = TeleBot(token=TELEGRAM_TOKEN)
    # timestamp = int(time.time())
    timestamp = 0
    cycle_counter = 0
    while True:
        cycle_counter += 1
        print(f'Starting polling {cycle_counter}...')
        try:
            check_tokens()
            payload = {'from_date': timestamp}
            homeworks = get_api_answer(payload)
            check_response(homeworks)
            homeworks_list = homeworks['homeworks']
            if not homeworks_list:
                logging.debug(f'Отсутствие в ответе новых статусов.')
                send_message(bot, 'Обновлений нет')
            for homework in homeworks_list:
                status_update = parse_status(homework)
                send_message(bot, status_update)
            timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)
        except TokenMissing as error:
            logging.critical(f'{error}. Bot will stop now.')
            break
        except UnexpectedResponseType or ExpectedResponseKeyNotFound:
            continue
        except ValueError as error:
            logging.error(f'{error}. Check token')
            continue
        except UnexpectedHomeworkStatus as error:
            logging.error(f'{error}. Unexpected status! Verdict not found.')
            continue
            


if __name__ == '__main__':
    main()
