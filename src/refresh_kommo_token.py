import os
import requests
import json
from config import config as cfg
from .utilities import load_setups, update_api_setup, get_timestamp
from dotenv import load_dotenv


load_dotenv()


# Set headers
headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Kommo-oAuth-client/1.0'
}


EXCHANGE_AC = {
    'client_id': os.getenv('CLIENT_ID'),
    'client_secret': os.getenv('CLIENT_SECRET'),
    'grant_type': 'authorization_code',
    'code': os.getenv('CODE'),
    'redirect_uri': os.getenv('REDIRECT_URI'),
}


def update_token():
    api_setup = load_setups()
    token_data = {
        'client_id': api_setup['client_id'],
        'client_secret': api_setup['client_secret_key'],
        'grant_type': api_setup['grant_type'],
        'refresh_token': api_setup['refresh_token'],
        'redirect_uri': os.getenv('REDIRECT_URI'),
    }

    print('checking token...')
    current_time = get_timestamp()
    token_timestamp = api_setup['token_timestamp']
    expires_in = api_setup['expires_in']
    if expires_in < (current_time - token_timestamp):
        response = requests.post(cfg['TOKEN_URL'],
                                 headers=headers,
                                 data=json.dumps(token_data)
                                 )

        if response.status_code < 200 or response.status_code > 204:
            error_message = cfg['ERRORS'].get(response.status_code,
                                              'Undefined error')
            raise Exception(f'Error: {error_message}. '
                            f'Error code: {response.status_code}')

        print('the token is being updated and recorded!')
        response_data = response.json()
        access_token = response_data['access_token']
        refresh_token = response_data['refresh_token']
        expires_in = response_data['expires_in']
        token_timestamp = current_time
        to_save = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': expires_in,
            'token_timestamp': token_timestamp
        }
        print('save new token...')
        update_api_setup(to_save)
    else:
        print('token is still valid')


def exchange_authorization_code():
    """
    Exchange of the authorization code to access token and refresh token

    !!! WARNING !!!
    before starting, you need to fill the EXCHANGE_AC constant with actual
    data.

    """
    current_time = get_timestamp()
    response = requests.post(cfg['TOKEN_URL'], headers=headers,
                             data=json.dumps(EXCHANGE_AC)
                             )
    if response.status_code < 200 or response.status_code > 204:
        error_message = cfg['ERRORS'].get(response.status_code,
                                          'Undefined error')
        raise Exception(f'Error: {error_message}. '
                        f'Error code: {response.status_code}')

    print('the token is being updated and recorded!')
    response_data = response.json()
    access_token = response_data['access_token']
    refresh_token = response_data['refresh_token']
    expires_in = response_data['expires_in']
    token_timestamp = current_time
    to_save = {
        'client_id': EXCHANGE_AC['client_id'],
        'client_secret': EXCHANGE_AC['client_secret'],
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': expires_in,
        'token_timestamp': token_timestamp
    }
    print('save new token...')
    update_api_setup(to_save)
