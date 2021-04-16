import time
import datetime
import data_loader as loader
import stat_delivery_time as deliver
import headers as hd

import os
import requests
from requests.auth import HTTPBasicAuth


class PreProcessingError(Exception):
    """ Ошибки возникающие при
        предобработке данных
    """
    def __init__(self, msg):
        self.message = msg


def test_recommend_to_1c():
    print(os.listdir('../../ordersprediction/tmp/'))
    headers = {'Content-type': 'application/json'}
    service_url = 'http://185.63.190.188/trade82new/hs/Service/SetPurchaseRecomendation/'
    path_json = '../../ordersprediction/tmp/output.json'

    def send_predictions(servie_url, path):
        response = requests.post(
            servie_url,
            auth=HTTPBasicAuth('Web', 'WebMarket'),
            data=open(path, 'rb'),
            headers=headers,
            timeout=540
        )
        if response.ok:
            print('Рекомендации успешно отправлены на сервер 1С!')

    send_predictions(service_url, path_json)


def main():
    ts = time.time()
    data_loader = loader.DataLoader()
    delivery_time = deliver.StatDeliveryTime()

    print(
        hd.LOG_MESSAGES['start_service'],
        datetime.datetime.now(),
        hd.LOG_MESSAGES['separating_line']
    )

    # test_recommend_to_1c()

    # Загружаем ежедневные исторические данные
    deliv, is_new_data, lst_date = data_loader.load_data()

    if is_new_data:
        # Отправим статистику по срокам доставок + графики
        delivery_time.get_statistics(deliv)
        delivery_time.get_stat_for_graphics(deliv, lst_date)

    print(
        hd.LOG_MESSAGES['stop_service'], datetime.datetime.now(),
        hd.LOG_MESSAGES['operating_time'] % ((time.time() - ts) / 60),
        hd.LOG_MESSAGES['separating_line']
    )


if __name__ == '__main__':
    while True:
        main()
        time.sleep(hd.SERVICE_DELAY['one_week'])
