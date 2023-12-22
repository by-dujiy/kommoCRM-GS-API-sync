import os
import requests
import time
from config import config as cfg
from .utilities import load_setups, get_next_session_time
from .gs_api import update_new_ord_id, get_tables
from .logger import exc_log, call_log, result_log
from dotenv import load_dotenv


load_dotenv()


table_list = {}
NETLOC = os.getenv('OWNER_NETLOC')


def _get_headers():
    call_log()
    api_setups = load_setups()
    access_token = api_setups['access_token']
    return {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': 'Kommo-oAuth-client/1.0'
    }


def _status_error_handler(response):
    """
    checks the server response for errors. If an error is found,
    throws a message to the terminal

    :param response:
    :return:
    """
    call_log(response.url)
    if response.status_code < 200 or response.status_code > 204:
        error_message = cfg['ERRORS'].get(response.status_code,
                                          'Undefined error')
        raise Exception(f'Error: {error_message}. '
                        f'Error code: {response.status_code}')


def _kommo_post_requester(url, body):
    call_log(url, body)
    while True:
        try:
            response = requests.post(url, headers=_get_headers(), json=body)
            time.sleep(cfg['SLEEP_TIME'])
            _status_error_handler(response)
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])

    result_log(response.json())
    return response.json()


def _write_psy_name(psy_list, psy_name):
    """
    write correct psy name
    """
    result = ''
    call_log(psy_list, psy_name)
    if psy_name not in psy_list:
        result = 'not_found'
    else:
        result = psy_name
    result_log(result)
    return result


def _get_leads_list(ts):
    """
    request a list of orders via api
    if response status == 204 - return empty list

    :param ts: the timestamp of the last connection to CRM
    :return: list of dictionaries containing information on orders
    :rtype: list[dict]
    """

    call_log(ts)
    url = (f'https://{NETLOC}/api/v4/leads?with=contacts&filter'
           f'[updated_at][from]={str(ts)}')
    while True:
        try:
            response = requests.get(url, headers=_get_headers())
            time.sleep(cfg['SLEEP_TIME'])
            _status_error_handler(response)
            if response.status_code == 204:
                result = []
                break
            else:
                result = response.json()['_embedded']['leads']
                break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])
    result_log(result)
    return result


def _get_contact(contact_id: int):
    """
    request contact id via api.
    has runtime delay 0.2sec

    :param contact_id:
    :return: contacts data
    :rtype: dict
    """

    call_log(contact_id)
    url = f'https://{NETLOC}/api/v4/contacts/{contact_id}'
    time.sleep(cfg['SLEEP_TIME'])
    while True:
        try:
            response = requests.get(url, headers=_get_headers())
            time.sleep(cfg['SLEEP_TIME'])
            _status_error_handler(response)
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
        time.sleep(cfg['DELAY_TIME'])
    result_log(response.json())
    return response.json()


def _parse_contact(contact_id: int):
    """
    contacts parser
    :param contact_id:
    :return:
    """

    call_log(contact_id)
    phone = ''
    email = ''
    rs = ''
    tg = ''
    subscribe = ''
    new_payment = ''
    contact_data = _get_contact(contact_id)
    name = contact_data.get('name')
    custom_fields = contact_data.get('custom_fields_values')
    if custom_fields is not None:
        for item in custom_fields:
            if item.get('field_id') == cfg['CONTACT_FIELDS'].get('PHONE'):
                phone = item.get('values', [{}])[0].get('value')
            if item.get('field_id') == cfg['CONTACT_FIELDS'].get('EMAIL'):
                email = item.get('values', [{}])[0].get('value')
            if item.get('field_id') == cfg['CONTACT_FIELDS'].get('R_S'):
                rs = item.get('values', [{}])[0].get('value')
            if item.get('field_id') == cfg['CONTACT_FIELDS'].get('TELEGRAM'):
                tg = item.get('values', [{}])[0].get('value')
            if item.get('field_id') == cfg['CONTACT_FIELDS'].get('SUBSCRIBE'):
                subscribe = item.get('values', [{}])[0].get('value')
            if item.get('field_id') == cfg['CONTACT_FIELDS'].get('NEW_PAYMENT'):
                new_payment = item.get('values', [{}])[0].get('value')

    result = {
        'name': name,
        'phone': phone,
        'email': email,
        'remaining_session': rs,
        'telegram': tg,
        'subscription': subscribe,
        'new_payment': new_payment
        }
    result_log(result)
    return result


def _parse_data(data: dict, status_list: dict) -> dict:
    """
    extracts the required data for each order from the received api response

    :param data: api response
    :param status_list: order status codes
    :return: list of values to upload to google spreadsheet
    """

    call_log(data, status_list)
    psy_list = [item for item in table_list.keys()]
    psy_name = ''
    next_session = ''
    pre_session = ''
    order_id = data.get('id')
    status_id = data.get('status_id')
    updated_at = data.get('updated_at')
    created_at = data.get('created_at')
    contact_id = data.get('_embedded', {}).get('contacts', [{}])[0].get('id')
    contact = _parse_contact(contact_id)
    custom_fields_values = data.get('custom_fields_values')
    if custom_fields_values is not None:
        for item in custom_fields_values:
            if item.get('field_id') == cfg['LEADS_FIELDS'].get('PSY'):
                psy_name = item.get('values', [{}])[0].get('value')
            if item.get('field_id') == cfg['LEADS_FIELDS'].get('NEXT_SESSION'):
                next_session = int(item.get('values', [{}])[0].get('value'))
            if item.get('field_id') == cfg['LEADS_FIELDS'].get('PREV_SESSION'):
                pre_session = int(item.get('values', [{}])[0].get('value'))

    result = {
        'id': order_id,
        'status': status_list[status_id],
        'updated': updated_at,
        'created': created_at,
        'contact': contact,
        'psy': psy_name,
        'previous_session': pre_session,
        'next_session': next_session
        }
    result_log(result)
    return result


def get_pipelines():
    """
    get a list of codes that indicate orders

    :return: dict with codes that indicate orders status
    :rtype: dict
    """
    global table_list
    table_list = get_tables()
    call_log(table_list)
    url = f'https://{NETLOC}/api/v4/leads/pipelines'
    response = _get_kommo_response(url)
    response_data = response.json()['_embedded']['pipelines']
    result = {}
    for item in response_data:
        name_pipeline = item.get('name')
        embedded_statuses = item.get('_embedded', {}).get('statuses')
        if embedded_statuses:
            for item_pip in embedded_statuses:
                result[item_pip.get('id')] = (f"{name_pipeline}: "
                                              f"{item_pip.get('name')}")
    result_log(result)
    return result


def receive_orders(pipelines):
    """
    composes the list of orders from leads and pipelines received from CRM.
    load timestamp last update from api_setup
    receives all necessary data (leads, statuses)
    updates the time stamp if new orders have been received


    :return: list of orders
    :rtype: list[dict]
    """
    call_log(pipelines)
    crm_ts = load_setups()['crm_timestamp']
    leads = _get_leads_list(crm_ts)
    result = [_parse_data(lead, pipelines) for lead in leads]
    result_log(result)
    return result


def _kommo_patch_request(url, body):
    call_log(url, body)
    while True:
        try:
            response = requests.patch(url, headers=_get_headers(), json=body)
            time.sleep(cfg['SLEEP_TIME'])
            _status_error_handler(response)
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])
    result_log(response.json())
    return response


def _decrease_pipeline(gs_order):
    call_log(gs_order)
    pip_statuses = get_pipelines()
    order_stat_id = 0
    stat_list = [key for key in pip_statuses.keys()]
    for key, val in pip_statuses.items():
        if val == gs_order.get('status'):
            order_stat_id = key
            break

    stat_index = stat_list.index(order_stat_id) - 1
    if stat_index < 1:
        stat_index = 1

    result_log(stat_list[stat_index])
    return stat_list[stat_index]


def _patch_order_ps(gs_order):
    """
    patching previous session datetime and pipeline status
    """
    call_log(gs_order)
    url = f'https://{NETLOC}/api/v4/leads'
    prev_sess = 683042400 if gs_order.get('prev_sess') == '' else gs_order.get('prev_sess')
    body = [
        {
            "id": gs_order['id'],
            "status_id": 58747787,
            "custom_fields_values": [
                {
                    "field_id": cfg.get('LEADS_FIELDS')['PREV_SESSION'],
                    "values": [
                        {
                            "value": prev_sess
                        }
                    ]
                }
            ]
        }
    ]
    return _kommo_patch_request(url, body)


def _kommo_patch_ns(gs_order):
    """
    patching next session datetime
    """
    call_log(gs_order)
    url = f'https://{NETLOC}/api/v4/leads'
    next_sess = 683042400 if gs_order.get('prev_sess') == '' else gs_order.get('prev_sess')
    body = [
        {
            "id": gs_order['id'],
            "custom_fields_values": [
                {
                    "field_id": cfg.get('LEADS_FIELDS')['NEXT_SESSION'],
                    "values": [
                        {
                            "value": next_sess
                        }
                    ]
                }
            ]
        }
    ]
    return _kommo_patch_request(url, body)


def _kommo_patch_sessions(gs_order):
    call_log(gs_order)
    url = f'https://{NETLOC}/api/v4/leads'

    prev_sess = 683042400 if gs_order.get('prev_sess') == '' else gs_order.get('prev_sess')
    next_sess = 683042400 if gs_order.get('prev_sess') == '' else gs_order.get('prev_sess')

    body = [
        {
            "id": gs_order['id'],
            "status_id": 58747787,
            "custom_fields_values": [
                {
                    "field_id": cfg.get('LEADS_FIELDS')['PREV_SESSION'],
                    "values": [
                        {
                            "value": prev_sess
                        }
                    ]
                },
                {
                    "field_id": cfg.get('LEADS_FIELDS')['NEXT_SESSION'],
                    "values": [
                        {
                            "value": next_sess
                        }
                    ]
                }
            ]
        }
    ]
    return _kommo_patch_request(url, body)


def _get_kommo_response(request_url):
    """
    request information from kommo-crm
    """
    call_log(request_url)
    while True:
        try:
            response = requests.get(request_url, headers=_get_headers())
            time.sleep(cfg['SLEEP_TIME'])
            _status_error_handler(response)
            break
        except (requests.RequestException, Exception) as e:
            exc_log(e)
            time.sleep(cfg['DELAY_TIME'])
    result_log(response.json())
    return response


def _request_cont_by_name(contact_name):
    call_log(contact_name)
    url = (f'https://{NETLOC}/api/v4/'
           f'contacts?filter[name]={contact_name}')
    response = requests.get(url, headers=_get_headers())

    if response.status_code == 204:
        result = []
    else:
        result = response.json()['_embedded']['contacts']
    result_log(result)
    return result


def _add_new_cont(cont_data):
    call_log(cont_data)

    url = f'https://{NETLOC}/api/v4/contacts'
    body = [
        {
            "name": cont_data.get('name'),
            "custom_fields_values": [
                {
                    "field_id": 781808,
                    "values": [
                        {
                            "value": cont_data.get('email')
                        },

                    ]
                },
                {
                    "field_id": 781806,
                    "values": [
                        {
                            "value": cont_data.get('phone')
                        }
                    ]
                },

            ]
        }
    ]
    data = _kommo_post_requester(url, body)
    contact_id = data['_embedded']['contacts'][0]['id']
    result_log(contact_id)
    return contact_id


def _add_new_order(order_data, cont_id):
    call_log(order_data, cont_id)
    url = f'https://{NETLOC}/api/v4/leads'
    body = [
        {
            "name": f"{order_data.get('name')} - {order_data.get('email')}",
            "status_id": 58747783,
            "custom_fields_values": [
                {
                    "field_id": 998149,
                    "values": [
                        {
                            "value": order_data.get('psy')
                        }
                    ]
                },
                {
                    "field_id": 998147,
                    "values": [
                        {
                            "value": get_next_session_time(
                                order_data.get('next_sess')
                            )
                        }
                    ]
                }
            ],
            "_embedded": {
                "contacts": [
                    {
                        "id": cont_id
                    }
                ]
            }
        }
    ]
    data = _kommo_post_requester(url, body)
    lead_id = data['_embedded']['leads'][0]['id']
    result_log(lead_id)
    return lead_id


def _create_in_kommo(order):
    call_log(order)
    result = []
    cont_data = _request_cont_by_name(order.get('name'))
    if not cont_data:
        contact_id = _add_new_cont(order)
        ord_id = _add_new_order(order, contact_id)
        result.append({'id': ord_id})
        update_new_ord_id(order.get('psy'),
                          order.get('row_num'),
                          ord_id)
    else:
        for cont in cont_data:
            custom_fields = cont.get('custom_fields_values')
            kommo_cont_email = ''
            for item in custom_fields:
                if item.get("field_name") == 'Email':
                    kommo_cont_email = item["values"][0]["value"]
                    break

            if order['email'] == kommo_cont_email:
                cont_id = cont.get('id')
                ord_id = _add_new_order(order, cont_id)
                result.append({'id': ord_id})
                update_new_ord_id(order.get('psy'),
                                  order.get('row_num'),
                                  ord_id)


def _request_order(order_id):
    call_log(order_id)
    url = (f'https://{NETLOC}/api/v4/'
           f'leads?with=contacts&filter[id]={order_id}')
    response = _get_kommo_response(url)

    if response.status_code == 204:
        result = []
    else:
        result = response.json()['_embedded']['leads'][0]

    result_log(result)
    return result


def processing_kommo(orders_data):
    call_log(orders_data)
    for order_data in orders_data:
        if order_data.get('gs_upd'):
            if order_data.get('id') == '':
                try:
                    _create_in_kommo(order_data)
                except Exception as e:
                    exc_log(e)
            else:
                kommo_order = _request_order(order_data.get('id'))
                order_custom_fields = kommo_order.get('custom_fields_values')
                prev_time = False
                pt_no_exist = True
                pt_change = False
                nt_change = False

                if order_custom_fields:
                    for item in kommo_order.get('custom_fields_values'):
                        if order_data.get('prev_sess'):
                            prev_time = True
                            if item.get('field_id') == cfg.get(
                                    'LEADS_FIELDS')['PREV_SESSION']:
                                pt_no_exist = False
                                if item.get('values')[0]['value'] != order_data.get(
                                        'prev_sess'):
                                    pt_change = True
                        if item.get('field_id') == cfg.get(
                                'LEADS_FIELDS')['NEXT_SESSION']:
                            if item.get('values')[0]['value'] != order_data.get(
                                    'next_sess'):
                                nt_change = True

                if prev_time and (pt_no_exist or pt_change) and nt_change:
                    res = _kommo_patch_sessions(order_data)
                elif prev_time and (pt_no_exist or pt_change):
                    res = _patch_order_ps(order_data)
                elif nt_change:
                    res = _kommo_patch_ns(order_data)
