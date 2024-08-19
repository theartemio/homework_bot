

from pprint import pprint
import os
import requests
import time

from dotenv import load_dotenv

from telebot import TeleBot, types
import logging



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
    level=logging.INFO,
    filename='main.log',
    filemode='a'
)

class TokenNotAccessible(Exception):
    def __str__(self):
        return 'Токен недоступен!'


class UnexpectedResponse(Exception):
    def __str__(self):
        return 'Некорректный ответ сервиса!'


def check_tokens():
    tokens = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
              'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
              'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
              }
    for token in tokens:
        if not tokens[token]:
            logging.critical('Отсутствует обязательных переменных окружения во время запуска бота') 
            raise TokenNotAccessible
            


def send_message(bot, message):
    '''
    Отправляет сообщение в Telegram-чат, определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра: экземпляр класса TeleBot и строку с текстом сообщения.
    '''
    chat_id = TELEGRAM_CHAT_ID
    try:
        bot.send_message(chat_id=chat_id, text=message)
        logging.debug('Удачная отправка любого в Telegram')
    except Exception as error:
        logging.error(f'Ошибка {error}')
         


def get_api_answer(timestamp):
    'Получает ответ, содержащий список домашек с изменившимся статусом на момент от timestamp до настоящего времени'
    try:
        homework_statuses = requests.get(url=ENDPOINT, headers=HEADERS, params=timestamp)
    except Exception as error:
        logging.error(f'Недоступен эндпоинт https://practicum.yandex.ru/api/user_api/homework_statuses/. Ошибка: {error}')
    homework_statuses_json = homework_statuses.json()
    homeworks = homework_statuses_json['homeworks']
    return homeworks


def check_response(response):
    reponse_type = type(response)
    # Залогировать: отсутствие ожидаемых ключей в ответе API (уровень ERROR);
    if reponse_type == list:
        return True


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
    timestamp = int(time.time())
    check_tokens()
    while True:
        try:
            status = f'Проверяю период от {timestamp} до {int(time.time())}'
            send_message(bot, status)
            payload = {'from_date': timestamp}
            homeworks = get_api_answer(payload)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text='Ответ API получен')
            if not len(homeworks):
                logging.debug(f'Отсутствие в ответе новых статусов.')
                send_message(bot, 'Обновлений нет')
            for homework in homeworks:
                status_update = parse_status(homework)
                print(status_update)
                send_message(bot, status_update)
            timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print(message)


if __name__ == '__main__':
    main()
