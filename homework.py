import logging
import os
import requests
import sys
import telegram
import time
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
    for token in (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN):
        if token is None:
            logging.critical(
                'Отсутствуют обязательные переменные окружения: '
                ' программа принудительно остановлена.'
            )
            sys.exit()


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        logging.debug(
            f'Попытка отправить сообщение: {message}'
        )
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Бот отправил сообщение')
    except Exception as error:
        logging.error(error)


def get_api_answer(timestamp):
    """Функция опроса API яндекс практикум."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != 200:
            logging.error(
                f'Ошибка сервера {response.status_code}.'
            )
            raise ValueError('Неверный статус ответа.')
        else:
            return response.json()

    except requests.RequestException as error:
        logging.debug(error)


def check_response(response):
    """Проверка запроса."""
    if 'homeworks' not in response:
        raise TypeError('В запросе нет домашних работ.')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('Полученные данные не являются списком.')
    return response['homeworks']


def parse_status(homework):
    """Проверка статуса домашней работы."""
    if 'status' not in homework:
        raise KeyError('В домашней работе отсутвует статус.')
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise KeyError('Статус работы недокументирован.')
    verdict = HOMEWORK_VERDICTS[status]
    if 'homework_name' not in homework:
        raise KeyError('В домашней работе отсутвует название.')
    homework_name = homework['homework_name']
    return (
        f'Изменился статус проверки работы '
        f'"{homework_name}". {verdict}'
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
            logging.error(message)
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
