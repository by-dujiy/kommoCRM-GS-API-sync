import os
from dotenv import load_dotenv


load_dotenv()


config = {
    'ERRORS': {
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not found',
        500: 'Internal server error',
        502: 'Bad gateway',
        503: 'Service unavailable',
    },
    'TIMEZONE': 'Europe/Kiev',
    'TOKEN_URL': os.getenv('KOMMO_TOKEN_URL'),
    'DT_FORMAT': '%d.%m.%Y %H:%M:%S',
    'SERVICE_ACCOUNT_FILE': os.getenv('GSA_FILE'),
    'API_SETUP_FILE': os.getenv('KOMMO_API_SETUP_FILE'),
    'SLEEP_TIME': 0.3,
    'MAX_RETRIES': 999,
    'DELAY_TIME': 20,
    'CONTACT_FIELDS': {
        'EMAIL': 781808,
        'PHONE': 781806,
        # Remaining_Sessions:
        'R_S': 1003654,
        'TELEGRAM': 1003662,
        'SUBSCRIBE': 1003664,
        'NEW_PAYMENT': 1007832
    },
    'LEADS_FIELDS': {
        'PSY': 998149,
        'NEXT_SESSION': 998147,
        'PREV_SESSION': 1003658
    },
    'GS_HEADER': {
        'ID':  'ID Заказа',
        'STATUS': 'Статус Заказа',
        'UPDATED': 'дата последнего обновления',
        'NAME': 'Фамилия Имя',
        'PHONE': 'Номер телефона',
        'EMAIL': 'Электронная почта',
        'PURCHASE_DATE': 'Дата покупки',
        'TG': 'Ник телеграм',
        'SUBSCRIBE': 'Абонемент',
        'REMAINING_SESSIONS': 'Остаток сессий',
        'PS_DATE': 'Дата предыдущей сессии',
        'PS_TIME': 'Время предыдущей сессии',
        'NS_DATE': 'Дата следующей сессии',
        'NS_TIME': 'Время следующей сессии',
        'NEW_PAYMENT': 'Новая оплата'
    }
}
