import logging
import os
import sys
import time
from http import HTTPStatus, client

import requests
from dotenv import load_dotenv
from telebot import TeleBot, apihelper

from exceptions import (ApiError, ExpectedKeyNotFound, RequestError,
                        TokenMissing, UnexpectedHomeworkStatus)

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

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def check_tokens():
    """Функция проверяет существование обязательных переменных окружения."""
    tokens = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
              'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
              'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
              }
    for token in tokens:
        if not tokens[token]:
            logger.critical(f'''Проблема с переменными окружения (токенами).
                            Обязательная переменная {token} не обнаружена!
                            Бот завершает работу''')
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
        logger.debug(f'Бот начинает отправку сообщения: {message}')
        bot.send_message(chat_id=chat_id, text=message)
        logger.debug(f'Успешно отправлено сообщение: {message}')
        return True
    except apihelper.ApiException or requests.RequestException as error:
        logger.error(error, exc_info=True)
        return False


def get_api_answer(timestamp):
    """
    Получает ответ API.
    Ответ должен содержать список домашек, статус
    которых поменялся в период от timestamp до настоящего времени.
    В качестве параметров функция принимает:
    timestamp - временную метку в формате Unix-времени
    """
    payload = {'from_date': timestamp}
    request_data = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': payload
    }
    logger.debug(f'''Получаем ответ API.
                    Информация о запросе:
                    Адрес эндпоинта: {request_data['url']},
                    Headers: {request_data['headers']},
                    Параметры: {request_data['params']}''')
    try:
        homework_statuses = requests.get(url=request_data['url'],
                                         headers=request_data['headers'],
                                         params=request_data['params'])
        response_code = homework_statuses.status_code
        if response_code != HTTPStatus.OK:
            raise ApiError(response_code, client.responses[response_code])
        homework_statuses_json = homework_statuses.json()
        logger.debug('Ответ API получен')
        return homework_statuses_json
    except requests.RequestException as error:
        logger.error(error, exc_info=True)
        raise RequestError(error)


def check_type_and_keys(response, example, element_name):
    """
    Проверяет наличие ключей и типы их значений.
    Ключи должны соответствовать документации API сервиса Практикум.Домашка.
    В качестве параметров функция принимает:
    response - Элемент, который необходимо проверить
    example - Пример данных, с которыми необходимо сравнить response
    element_name - Название проверяемого элемента для сообщений об ошибках
    и логов
    """
    expected_type = dict
    if not isinstance(response, expected_type):
        reponse_type = type(response)
        raise TypeError(f'''Некорректный {element_name}.
                        Ожидался {expected_type.__name__},
                        получен {reponse_type.__name__}.''')
    logger.debug(f'''Тип {element_name} проверен:
                 полученный тип соответствует ожидаемому.''')
    for key, value in example.items():
        if key not in response.keys():
            raise ExpectedKeyNotFound(key, element_name)
        if not isinstance(response[key], value):
            raise TypeError(f'''Некорректный {element_name}.
                            Ожидался тип значения {key} равный {value},
                            получен {type(response[key])}''')
    logger.debug(f'''{element_name} проверен.
                 Все ожидаемые ключи {example.keys()}
                 на месте.''')


def check_response(response):
    """
    Проверяет ответ API на соответствие документации.
    Если проверка прошла успешно, функция
    возвращает список с домашками.
    В качестве параметра функция получает:
    response - ответ API, приведённый к типам данных Python.
    """
    response_keys_and_types = {'homeworks': list,
                               'current_date': int,
                               }
    checking = 'Ответ API'
    check_type_and_keys(response, response_keys_and_types, checking)
    homework_list = response['homeworks']
    logger.debug(f'''Ответ API проверен.
                 Все ожидаемые ключи {response_keys_and_types.keys()}
                 на месте.''')
    return homework_list


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
    logger.debug(f'''Получен статус {homework_status} для работы
                 {homework_name}''')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    logger.info(f'Бот начал работу. Первая временная метка: {timestamp}.')
    send_message(bot, 'Бот начал работу!')
    last_message = None
    check_tokens()
    while True:
        try:
            homeworks = get_api_answer(timestamp)
            homeworks_list = check_response(homeworks)
            if not homeworks_list:
                logger.debug(f'''Проверен период от {timestamp}
                             до {int(time.time())}.
                             В ответе отсутствуют обновления статусов
                              домашки (список работ под ключом
                              "homeworks" пуст).''')
            for homework in homeworks_list:
                try:
                    status_update = parse_status(homework)
                    message_sent = send_message(bot, status_update)
                    if message_sent:
                        timestamp = homeworks['current_date']
                except UnexpectedHomeworkStatus as error:
                    send_message(bot, f'Возникла ошибка! {error}')
                    logger.error(error, exc_info=True)
                    continue
        except (ExpectedKeyNotFound,
                TypeError,
                ApiError) as error:
            logger.error(error, exc_info=True)
            error_message = f'Возникла ошибка! {error}'
            if last_message != error_message:
                send_message(bot, error_message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s, %(name)s, %(levelname)s, %(message)s',
        level=logging.DEBUG,
        filename='homework_bot.log',
        filemode='a'
    )
    try:
        main()
    except TokenMissing as error:
        sys.exit(f'Отсутствует обязательная переменная окружения. {error}.')
