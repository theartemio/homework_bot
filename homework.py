
import logging
import os
import sys
import time

import requests
from datetime import datetime
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import (ApiError, ExpectedKeyNotFound, TokenMissing,
                        UnexpectedHomeworkStatus, UnexpectedResponseType)

load_dotenv()

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


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename='homework_bot.log',
    filemode='a'
)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

def check_tokens():
    """
    Функция проверяет существование обязательных переменных окружения.
    Проверяемые переменные:
    PRACTICUM_TOKEN
    TELEGRAM_TOKEN
    TELEGRAM_CHAT_ID
    """
    tokens = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
              'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
              'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
              }
    for token in tokens:
        if not tokens[token]:
            raise TokenMissing(token)


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram-чат.
    Чат определяется переменной окружения TELEGRAM_CHAT_ID.
    В качестве параметров функция принимает:
    bot - экземпляр класса TeleBot
    message - строку с текстом сообщения
    """
    chat_id = TELEGRAM_CHAT_ID
    try:
        bot.send_message(chat_id=chat_id, text=message)
        logger.debug(f'Успешно отправлено сообщение: {message}')
    except Exception as error:
        logger.error(error, exc_info=True)


def get_api_answer(timestamp):
    """
    Получает ответ API.
    Ответ должен содержать список домашек, статус
    которых поменялся в период от timestamp до настоящего времени.
    В качестве параметров функция принимает:
    timestamp - временную метку в формате Unix-времени
    """
    try:
        homework_statuses = requests.get(url=ENDPOINT,
                                         headers=HEADERS,
                                         params=timestamp)
        if homework_statuses.status_code != 200:
            raise ApiError(homework_statuses.status_code)
        homework_statuses_json = homework_statuses.json()
        return homework_statuses_json
    except requests.RequestException as error:
        logger.error(error, exc_info=True)


def check_type_and_keys(response, example_element, element_name):
    """
    Проверяет наличие ключей и типы их значений.
    Ключи должны соответствовать документации API сервиса Практикум.Домашка.
    В качестве параметров функция принимает:
    response - Элемент, который необходимо проверить
    example_element - Пример данных, с которыми необходимо сравнить response
    element_name - Название проверяемого элемента для сообщений об ошибках
    и логов
    """
    reponse_type = type(response)
    expected_type = dict
    if not isinstance(response, expected_type):
        raise TypeError(f'''Некорректный {element_name}.
                        Ожидался {expected_type.__name__},
                        получен {reponse_type.__name__}.''')
    logger.info(f'''Тип {element_name} проверен:
                 полученный тип {reponse_type}
                 соответствует ожидаемому.''')
    for key, value in example_element.items():
        if key not in response.keys():
            raise ExpectedKeyNotFound(key, element_name)
        if not isinstance(response[key], value):
            raise TypeError(f'''Некорректный {element_name}.
                            Ожидался тип значения {key} равный {value},
                            получен {type(response[key])}''')
    logger.info(f'''{element_name} проверен.
                 Все ожидаемые ключи {example_element.keys()}
                 на месте.''')


def check_response(response):
    """
    Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает:
    response - ответ API, приведённый к типам данных Python.
    """
    response_keys_and_types = {'homeworks': list,
                               'current_date': int,
                               }
    checking = 'Ответ API'
    check_type_and_keys(response, response_keys_and_types, checking)
    logger.info(f'''Ответ API проверен.
                 Все ожидаемые ключи {response_keys_and_types.keys()}
                 на месте.''')


def parse_status(homework):
    """
    Извлекает статус домашки.
    Извлекает из словаря с информацией о конкретной домашней работе
    статус этой работы.
    В случае успеха функция возвращает подготовленную для отправки
    в Telegram строку, содержащую один из вердиктов словаря HOMEWORK_VERDICTS.
    В качестве параметра функция получает:
    homework - словарь с информацией о домашней работе,
    описанный в документации к API
    """
    homework_keys_and_types = {'homework_name': str,
                               'status': str
                               }
    checking = 'Элемент из списка с домашкой'
    check_type_and_keys(homework, homework_keys_and_types, checking)
    homework_status = homework['status']
    homework_name = homework['homework_name']
    if homework_status not in HOMEWORK_VERDICTS.keys():
        raise UnexpectedHomeworkStatus(homework_status)
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    timestamp = 0
    while True:
        try:
            send_message(bot, f'''Проверяю период
                         от {timestamp} до {int(time.time())}''')
            
            check_tokens()
            payload = {'from_date': timestamp}
            homeworks = get_api_answer(payload)
            check_response(homeworks)
            homeworks_list = homeworks['homeworks']
            if not homeworks_list:
                logger.debug('''В ответе отсутствуют обновления статусов
                              домашки (список работ под ключом
                              "homeworks" пуст).''')
                send_message(bot, '''Проверен период от  
                             Обновлений пока нет''')
            for homework in homeworks_list:
                try:
                    status_update = parse_status(homework)
                    send_message(bot, status_update)
                except UnexpectedHomeworkStatus as error:
                    send_message(bot, f'Возникла ошибка! {error}')
                    logger.error(error, exc_info=True)
                    continue
            timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)
        except TokenMissing as error:
            logger.critical(error, exc_info=True)
            send_message(bot, f'Возникла ошибка! {error}')
            break
        except (UnexpectedResponseType,
                ExpectedKeyNotFound,
                TypeError,
                ApiError) as error:
            send_message(bot, f'Возникла ошибка! {error}')
            logger.error(error, exc_info=True)
            time.sleep(RETRY_PERIOD)
            continue


if __name__ == '__main__':
    main()
