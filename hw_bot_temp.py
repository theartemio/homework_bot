

from pprint import pprint
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
)


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 15
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
            token_error_message = f'Token missing: {token}'
            logging.critical(token_error_message)
            raise TokenMissing

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
        logging.debug(f'''Message sent successfully. Message text: {message}''')
    except Exception as error:
        logging.error(f'Message not sent: {error}')


def get_api_answer(timestamp):
    '''Получает ответ, содержащий список домашек с изменившимся статусом
    на момент от timestamp до настоящего времени. Принимает аргументы:
    timestamp - временную метку
    '''
    try:
        homework_statuses = requests.get(url=ENDPOINT, headers=HEADERS, params=timestamp)
    except Exception as error:
        logging.error(f'Endpoint {ENDPOINT} unavailable. Error: {error}')
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
    logging.debug(f'API response checked. response type: {reponse_type} is ok')
    for key in response_expected_keys:
        if key not in response.keys():
            logging.error(f'Некорректный ответ API. В ответе отсутствует ключ {key}.')
            raise ExpectedResponseKeyNotFound
    logging.debug(f'API response checked. All expected keys ({response_expected_keys}) found')


def parse_status(homework):
    '''
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка домашних работ.
    В случае успеха функция возвращает подготовленную для отправки в Telegram строку,
    содержащую один из вердиктов словаря HOMEWORK_VERDICTS
    '''
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
        finally:
            print('sleeping now...')
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
