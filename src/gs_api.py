import gspread
from .utilities import time_formatter, dt_parser, load_setups, to_timestamp
from config import config as cfg
import time
from .logger import exc_log, call_log, result_log
import requests


API_SETUPS = load_setups()
TAB_KEY = API_SETUPS['tab_key']
SA_FILE = cfg['SERVICE_ACCOUNT_FILE']

ID = cfg['GS_HEADER'].get('ID')
STATUS = cfg['GS_HEADER'].get('STATUS')
UPDATED = cfg['GS_HEADER'].get('UPDATED')
NAME = cfg['GS_HEADER'].get('NAME')
PHONE = cfg['GS_HEADER'].get('PHONE')
EMAIL = cfg['GS_HEADER'].get('EMAIL')
PURCHASE_DATE = cfg['GS_HEADER'].get('PURCHASE_DATE')
TG = cfg['GS_HEADER'].get('TG')
SUBSCRIBE = cfg['GS_HEADER'].get('SUBSCRIBE')
REMAINING_SESSIONS = cfg['GS_HEADER'].get('REMAINING_SESSIONS')
PS_DATE = cfg['GS_HEADER'].get('PS_DATE')
PS_TIME = cfg['GS_HEADER'].get('PS_TIME')
NS_DATE = cfg['GS_HEADER'].get('NS_DATE')
NS_TIME = cfg['GS_HEADER'].get('NS_TIME')
NEW_PAYMENT = cfg['GS_HEADER'].get('NEW_PAYMENT')


table_list = {}


def _get_gs():
    call_log()
    while True:
        try:
            res = gspread.service_account(filename=SA_FILE)
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])
    result_log(res)
    return res


gs = _get_gs()


def _get_sh():
    call_log()
    while True:
        try:
            res = gs.open_by_key(TAB_KEY)
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])
    result_log(res)
    return res


sh = _get_sh()


def get_tables():
    call_log()
    while True:
        try:
            ws = sh.get_worksheet(0)
            records = ws.get_all_records()
            time.sleep(cfg['SLEEP_TIME'])
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])
    result = {item['Психолог']: item['ссылка на таблицу']
              for item in records if item.get('загрузка')}
    result_log(result)
    return result


def _get_tab_worksheet(name):
    call_log(name)
    while True:
        try:
            sht = gs.open_by_url(table_list.get(name))
            time.sleep(0.1)
            ws = sht.get_worksheet(0)
            time.sleep(cfg['SLEEP_TIME'])
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            return None
    result_log(ws)
    return ws


def _find_empty_row(worksheet):
    call_log(worksheet)
    while True:
        try:
            rows = worksheet.get_all_values()
            time.sleep(cfg['SLEEP_TIME'])
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])

    for index, row in enumerate(rows):
        if all(cell == '' for cell in row):
            return index + 1
    result =  len(rows) + 1
    result_log(result)
    return result


def _get_col_letter(col_num):
    """
    Convert a column number to a column letter

    """
    call_log(col_num)
    letters = ""
    while col_num:
        col_num, remainder = divmod(col_num - 1, 26)
        letters = chr(65 + remainder) + letters

    result_log(letters)
    return letters


def _get_head_coord():
    """
    Returns the column coordinate
    """
    head_names = [
        ID,
        NAME,
        PHONE,
        EMAIL,
        TG,
        NEW_PAYMENT,
        SUBSCRIBE,
        STATUS,
        PURCHASE_DATE,
        REMAINING_SESSIONS,
        PS_DATE,
        PS_TIME,
        NS_DATE,
        NS_TIME,
        UPDATED,
        ]
    call_log(head_names)
    while True:
        try:
            sht = gs.open_by_url(next(iter(table_list.values())))
            headers = sht.get_worksheet(0).row_values(1)
            time.sleep(cfg['SLEEP_TIME'])
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])
    time.sleep(cfg['SLEEP_TIME'])
    result = []
    for col_name in head_names:
        if col_name in headers:
            # Convert the index to the corresponding letter format and return
            col_index = headers.index(col_name)
            col_letter = _get_col_letter(col_index + 1)
            result.append(col_letter)
    result_log(result)
    return result


def _create_row(order_data, row_num, head_coord):
    """
    creating a string in the required format
    for further recording in a Google spreadsheet
    """
    call_log(order_data, row_num, head_coord)
    ps_data, ps_time = dt_parser(order_data.get('previous_session'))
    ns_data, ns_time = dt_parser(order_data.get('next_session'))
    result = [
        {'range': f'{col}{row_num}', 'values': [[val]]}
        for col, val in zip(head_coord, [
            order_data.get('id'),
            order_data.get('contact')['name'],
            order_data.get('contact')['phone'],
            order_data.get('contact')['email'],
            order_data.get('contact')['telegram'],
            order_data.get('contact')['new_payment'],
            order_data.get('contact')['subscription'],
            order_data.get('status'),
            time_formatter(order_data.get('created')),
            order_data.get('contact')['remaining_session'],
            ps_data,
            ps_time,
            ns_data,
            ns_time,
            time_formatter(order_data.get('updated')),
        ])
    ]
    result_log(result)
    return result


def _add_new_orders(name: str, crm_orders: list, head_coord: list):
    """
    Add the new row into the Google Sheet.
    """
    call_log(name, crm_orders, head_coord)
    worksheet = _get_tab_worksheet(name)
    while True:
        try:
            empty_row = _find_empty_row(worksheet)
            time.sleep(cfg['SLEEP_TIME'])
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])
    time.sleep(cfg['SLEEP_TIME'])
    new_data = []
    for order in crm_orders:
        new_row = _create_row(order, empty_row, head_coord)
        new_data.append(new_row)
        empty_row += 1
    result_log(new_data)
    return new_data


def _update_exist_orders(crm_orders: list, head_coord: list):
    """
    Update the exist row into the Google Sheet.
    """
    upd_data = []
    call_log(crm_orders, head_coord)
    for order in crm_orders:
        new_row = _create_row(order, order.get('row_num'), head_coord)
        upd_data.append(new_row)
    result_log(upd_data)
    return upd_data


def _write_data(name, orders_data):
    """
    Writes data to the Google Sheet.
    """
    worksheet = _get_tab_worksheet(name)
    call_log(name, orders_data)
    for order in orders_data:
        worksheet.batch_update(order, value_input_option='user_entered')
        time.sleep(cfg['SLEEP_TIME'])


def update_new_ord_id(name, row_num, ord_id):
    call_log(name, row_num, ord_id)
    worksheet = _get_tab_worksheet(name)
    while True:
        try:
            worksheet.update_cell(row_num, 2, ord_id)
            # worksheet.update(f"B{row_num}", [[ord_id]])
            time.sleep(cfg['SLEEP_TIME'])
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])


def _delete_data(name, row_num):
    call_log(name, row_num)
    worksheet = _get_tab_worksheet(name)
    while True:
        try:
            worksheet.delete_row(row_num)
            time.sleep(cfg['SLEEP_TIME'])
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])


def get_gs_records():
    global table_list
    table_list = get_tables()
    call_log(table_list)
    all_rec = []
    for list_name in table_list.keys():
        upd_trigger = False
        worksheet = _get_tab_worksheet(list_name)
        if worksheet is None:
            continue
        time.sleep(0.1)
        while True:
            try:
                ws_rec = worksheet.get_all_records()
                time.sleep(0.1)
                break
            except (gspread.exceptions.APIError, Exception) as e:
                exc_log(e)
                time.sleep(cfg['DELAY_TIME'])
        for row_num, rec in enumerate(ws_rec, start=1):
            try:
                prev_sess_dt = to_timestamp(
                    str(rec.get(PS_DATE)),
                    str(rec.get(PS_TIME))
                )
            except (requests.RequestException, Exception) as e:
                exc_log(e)
                prev_sess_dt = 1672524000
            try:
                next_sess_dt = to_timestamp(
                    str(rec.get(NS_DATE)),
                    str(rec.get(NS_TIME))
                )
            except (requests.RequestException, Exception) as e:
                exc_log(e)
                next_sess_dt = 1672524000
            gs_upd = rec.get('Изменения google')
            all_rec.append({
                'id': rec.get(ID),
                'name': rec.get(NAME).strip(),
                'phone': rec.get(PHONE),
                'email': rec.get(EMAIL).strip(),
                'new_payment': rec.get(NEW_PAYMENT),
                'status': rec.get(STATUS),
                'gs_upd': gs_upd,
                'psy': list_name,
                'prev_sess': prev_sess_dt,
                'next_sess': next_sess_dt,
                'row_num': row_num+1
            })
            if gs_upd != '':
                upd_trigger = True
        if upd_trigger:
            _clear_first_col(worksheet)
        time.sleep(cfg['SLEEP_TIME'])
    result_log(all_rec)
    return all_rec


def patch_orders(gs_orders):
    """
    find updated row in gs and add it in list

    """
    call_log(gs_orders)
    result = []
    for order in gs_orders:
        if order['gs_upd'] != '':
            result.append(order)
    result_log(result)
    return result


def _clear_first_col(worksheet):
    """
    Clears data from the first column (except for the first row)
    for all existing worksheets in the Google Spreadsheet.
    """
    call_log(worksheet)
    while True:
        try:
            num_rows = worksheet.row_count
            clear_range = f'A2:A{num_rows}'
            worksheet.batch_update([{
                'range': clear_range,
                'values': [[''] for _ in range(num_rows - 1)]
            }])
            time.sleep(cfg['SLEEP_TIME'])
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])


def processing_gs_orders(kommo_orders, gs_orders):
    """
    compares orders crm and google spreadsheets

    """
    head_coord = _get_head_coord()
    call_log(kommo_orders, gs_orders)
    # create dicts where key - gs list name, list - list of orders
    to_update = {ws_name: [] for ws_name in table_list.keys()}
    to_append = {ws_name: [] for ws_name in table_list.keys()}
    to_delete = {ws_name: [] for ws_name in table_list.keys()}

    # orders num from GS for compare with orders from kommo
    gs_orders_id = [order['id'] for order in gs_orders]

    for k_ord in kommo_orders:
        if not k_ord['psy']:
            continue
        if k_ord['id'] not in gs_orders_id:
            to_append[k_ord['psy']].append(k_ord)
            continue
        gs_ord = next((o for o in gs_orders if o['id'] == k_ord['id']), None)
        if k_ord['psy'] != gs_ord['psy']:
            to_delete[gs_ord['psy']].append(gs_ord)
            to_append[k_ord['psy']].append(k_ord)
        else:
            k_ord['row_num'] = gs_ord.get('row_num')
            to_update[k_ord['psy']].append(k_ord)

    for list_name, ord_data in to_update.items():
        if not ord_data:
            continue
        upd_data = _update_exist_orders(ord_data, head_coord)
        _write_data(list_name, upd_data)

    for list_name, ord_data in to_append.items():
        if not ord_data:
            continue
        new_data = _add_new_orders(list_name, ord_data, head_coord)
        _write_data(list_name, new_data)

    for list_name, order_data in to_delete.items():
        if not order_data:
            continue
        sorted_orders = sorted(order_data, key=lambda x: x['row_num'])
        for order in reversed(sorted_orders):
            _delete_data(list_name, order.get('row_num'))
