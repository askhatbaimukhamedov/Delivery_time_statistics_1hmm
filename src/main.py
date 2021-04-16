import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
import time
import data_loader as loader
import stat_delivery_time as deliver
import headers as hd
import requests
from requests.auth import HTTPBasicAuth


class PreProcessingError(Exception):
    """ Ошибки возникающие при
        предобработке данных
    """
    def __init__(self, msg):
        self.message = msg


class ServiceLogger(object):
    """ Класс реализует логирование и
        протоколирования работы сервиса
    """
    def __init__(self):
        self.LOG_FILE = hd.PATH_DATA['info_messages']

    @staticmethod
    def __get_console_handler(formatter):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(formatter))
        return console_handler

    def __get_file_handler(self, formatter):
        file_handler = TimedRotatingFileHandler(self.LOG_FILE, when='midnight')
        file_handler.setFormatter(logging.Formatter(formatter))
        return file_handler

    def get_logger(self, logger_name, formatter):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.addHandler(self.__get_console_handler(formatter))
        logger.addHandler(self.__get_file_handler(formatter))
        logger.propagate = False
        return logger


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
    data_loader = loader.DataLoader()
    delivery_time = deliver.StatDeliveryTime()
    indent_log = ServiceLogger().get_logger(
        'indent', hd.INDENT_FORMAT_LOG
    )
    logger = ServiceLogger().get_logger(
        hd.LOG_MESSAGES['service_name'],
        hd.BASE_FORMAT_LOG
    )

    # test_recommend_to_1c()
    indent_log.info('just indent')
    logger.info(hd.LOG_MESSAGES['start_service'])

    # Загружаем ежедневные исторические данные
    deliv, is_new_data, lst_date = data_loader.load_data(logger)

    if is_new_data:
        # Отправим статистику по срокам доставок + графики
        delivery_time.get_statistics(deliv, logger)
        delivery_time.get_stat_for_graphics(deliv, lst_date, logger)

    logger.info(hd.LOG_MESSAGES['stop_service'])


if __name__ == '__main__':
    while True:
        main()
        time.sleep(hd.SERVICE_DELAY['one_week'])
