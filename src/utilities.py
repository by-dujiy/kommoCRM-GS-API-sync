from datetime import datetime, timedelta
from config import config as cfg
import json
import pytz
import re


def time_formatter(timestamp):
    """
    transform timestamp to human datetime format

    :param timestamp:
    :return: dt string
    """
    dt_object = datetime.fromtimestamp(timestamp)
    dt_object = dt_object + timedelta(hours=0)
    return dt_object.strftime(cfg.get('DT_FORMAT'))


def valid_true_tf(time_str: str) -> bool:
    # Регулярное выражение для проверки формата 'HH:MM:SS'
    pattern = r'^([01]?\d|2[0-3]):([0-5]?\d):([0-5]?\d)$'
    return bool(re.match(pattern, time_str))


def valid_false_tf(time_str: str) -> bool:
    # Регулярное выражение для проверки формата 'HH:MM'
    pattern = r'^([01]?\d|2[0-3]):([0-5]?\d)$'
    return bool(re.match(pattern, time_str))


def valid_time(time):
    if time.isdigit():
        if len(time) > 4:
            time = time[:4]
        time = time[:2] + ':' + time[2:]

    if len(time) > 5:
        time = time[:5]

    sep = find_sep(time)
    if sep != ':':
        time = time.replace(sep, ':')

    if valid_true_tf(time):
        t_time = time
    elif valid_false_tf(time):
        t_time = ':'.join([time, '00'])
    else:
        t_time = '00:00:00'
    return t_time


# def to_timestamp(dt_str: str) -> int:
#     """
#     transform datetime to timestamp format
#
#     :param dt_str:
#     :return: timestamp in integer representation
#     :rtype: int
#     """
#     if dt_str != ' ':
#         date, time = dt_str.split(' ')
#         dt_str = f"{date} {valid_time(time)}"
#         result = int(datetime.strptime(dt_str, cfg.get('DT_FORMAT')).timestamp())
#     else:
#         result = ''
#     return result


def find_sep(item):
    separators_list = [',', '-', ':', ';', '/', '\\', '.']
    for char in item:
        if char in separators_list:
            return char


# '1012023'
def valid_date(date_str: str):
    if date_str.isdigit():
        if len(date_str) > 8:
            date_str = date_str[:8]
        elif len(date_str) == 7:
            date_str = ''.join(['0', date_str])
        result = date_str[:2] + '.' + date_str[2:4] + '.' + date_str[4:]
    else:
        separator = find_sep(date_str)
        if len(date_str) > 10:
            date_str = date_str[:10]
        if separator != '.':
            result = date_str.replace(separator, '.')
        else:
            result = date_str
    return result


def to_timestamp(date_str: str, time_str: str) -> int:
    """
    transform datetime to timestamp format

    """
    if date_str != '' and time_str != '':
        dt_str = f"{valid_date(date_str)} {valid_time(time_str)}"
        result = int(datetime.strptime(dt_str, cfg.get('DT_FORMAT')).timestamp())
    else:
        result = ''
    return result


def dt_parser(dt: str) -> tuple[str | None, str | None]:
    """
    transform datetime from timestamp to human format and split
    :param dt: datetime in string representation
    :return: string data and string time or None
    """
    if dt:
        dt_d, dt_t = time_formatter(dt).split(' ')
    else:
        dt_d, dt_t = None, None
    return dt_d, dt_t


def update_api_setup(receive_data):
    """
    compares the incoming data with the data written in the file. If
    differences are found, overwrites the file with new incoming data

    :param receive_data: incoming parameters.
    :type receive_data: dict
    """
    with open(cfg['API_SETUP_FILE'], 'r') as file:
        file_data = json.load(file)

    to_rec = update_dict_data(file_data, receive_data)
    with open(cfg['API_SETUP_FILE'], 'w') as file:
        json.dump(to_rec, file, indent=4)


def upd_crm_timestamp(orders):
    """
    if there are new orders - records the date (timestamp) of the last update
    """
    if orders:
        max_updated = max(order['updated'] for order in orders)
        ts_data = {'crm_timestamp': max_updated+10}
        update_api_setup(ts_data)


def update_dict_data(main_dict: dict, incoming_dict: dict) -> dict:
    """
    compares the main dictionary with the incoming. if differences are found,
    it overwrites the main dictionary data with the data from the incoming
    dictionary.

    :param main_dict: basic data
    :type main_dict: dict
    :param incoming_dict: comparison data
    :type incoming_dict: dict
    :return: new dict data
    :rtype: dict
    """
    for key, value in incoming_dict.items():
        if key not in main_dict or main_dict[key] != value:
            main_dict[key] = value
    return main_dict


def load_setups():
    with open(cfg['API_SETUP_FILE'], 'r') as file:
        file_data = json.load(file)
    return file_data


def get_timestamp():
    current_time = datetime.now(pytz.timezone(cfg['TIMEZONE']))
    return int(current_time.timestamp())


def get_next_session_time(time_data):
    if time_data == '':
        result = get_timestamp()
    else:
        result = time_data
    return result
