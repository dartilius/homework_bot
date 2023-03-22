import telegram
import requests
from datetime import datetime
import time
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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


def check_tokens():
    """Проверка токенов."""
    if PRACTICUM_TOKEN is None:
        logging.critical(
            'Отсутствует обязательная переменная окружения: '
            'PRACTICUM_TOKEN - программа принудительно остановлена.'
        )
        exit()

    if TELEGRAM_TOKEN is None:
        logging.critical(
            'Отсутствует обязательная переменная окружения: '
            'TELEGRAM_TOKEN - программа принудительно остановлена.'
        )
        exit()

    if TELEGRAM_CHAT_ID is None:
        logging.critical(
            'Отсутствует обязательная переменная окружения: '
            'TELEGRAM_CHAT_ID - программа принудительно остановлена.'
        )
        exit()


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(
            f'Бот отправил сообщение: '
            f'{message}'
        )

    except Exception as error:
        logging.error(f'{error}')


def get_api_answer(timestamp):
    """Функция опроса API яндекс практикум."""
    payload = {'from_date': timestamp}
    try:
        requsest = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if requsest.status_code != 200:
            logging.error(
                f'ошибка сервера {requsest.status_code}'
            )
            raise f'Ошибка сервера {requsest.status_code}'
        else:
            return requsest.json()

    except Exeption as error:
        logging.error(f'Ошибка запроса {error}')


def check_response(response):
    """Проверка запроса."""
    try:
        homeworks = response['homeworks']
        if not isinstance(homeworks, list):
            raise TypeError('Полученые данные не являются списком')
        else:
            return response['homeworks']
    except:
        raise 'Нет поля homeworks'


def parse_status(homework):
    """Проверка статуса домашней работы."""
    try:
        verdict = HOMEWORK_VERDICTS[homework['status']]
        homework_name = homework['homework_name']
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'

    except Exeption:
        logging.debug(
            f'Статус работы отсутсвует'
        )


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    while True:
        timestamp = int(time.time())
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                status = parse_status(homework)
                send_message(bot, status)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print(message)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
