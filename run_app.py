import time
from datetime import datetime
import src
import os


def run_app():
    # checking the tokens validation for access to kommo-crm
    src.update_token()
    pip_statuses = src.get_pipelines()
    kommo_orders = src.receive_orders(pip_statuses)
    gs_rec = src.get_gs_records()
    src.processing_gs_orders(kommo_orders, gs_rec)
    src.processing_kommo(gs_rec)
    src.upd_crm_timestamp(kommo_orders)


if __name__ == '__main__':
    while True:
        run_app()
        print(f"sleep:  {datetime.now()}  - 60 sec")
        time.sleep(75)
        os.system('cls' if os.name == 'nt' else 'clear')

