import os
import sys
import logging
import time
import data_loader as loader
import stat_delivery_time as deliver
import headers as hd
import requests
from requests.auth import HTTPBasicAuth
from logging.handlers import TimedRotatingFileHandler

import pandas as pd


class PreProcessingError(Exception):
    """ Ошибки возникающие при
        предобработке данных
    """
    def __init__(self, msg):
        self.message = msg


class ServiceLogger(object):
    """ Класс реализует логирование и
        протоколирование работы сервиса
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


# def test_recommend_to_1c():
#     def send_predictions(path):
#         response = requests.post(
#             'http://185.63.190.188/trade82new/hs/Service/SetPurchaseRecomendation/',
#             auth=HTTPBasicAuth('Web', 'WebMarket'),
#             data=open(path, 'rb'),
#             headers={'Content-type': 'application/json'}
#         )
#         if response.ok:
#             print(f'успешно отправлен {path[28:]}!')
#
#     for item in range(11, 152):
#         path_json = f'../../ordersprediction/tmp/output{item}.json'
#         send_predictions(path_json)

def test_recommend_to_1c():
    def send_predictions(path):
        response = requests.post(
            'http://185.63.190.188/trade82new/hs/Service/SetPurchaseRecomendation/',
            auth=HTTPBasicAuth('Web', 'WebMarket'),
            data=open(path, 'rb'),
            headers={'Content-type': 'application/json'}
        )
        if response.ok:
            print(f'успешно отправлен {path[28:]}!')

    send_predictions('../../ordersprediction/tmp/output.json')


def main():
    data_loader = loader.DataLoader()
    delivery_time = deliver.StatDeliveryTime()
    indent_log = ServiceLogger().get_logger('indent', hd.INDENT_FORMAT_LOG)
    logger = ServiceLogger().get_logger(hd.LOG_MESSAGES['service_name'], hd.BASE_FORMAT_LOG)

    # test_recommend_to_1c()
    indent_log.info('just indent')
    logger.info(hd.LOG_MESSAGES['start_service'])

    # Загружаем ежедневные исторические данные
    deliv, is_new_data, lst_date = data_loader.load_data(logger)

    if is_new_data:
        # Отправим статистику по срокам доставок + графики
        delivery_time.get_statistics(deliv, lst_date, logger)
        delivery_time.get_stat_for_graphics(deliv, lst_date, logger)

    logger.info(hd.LOG_MESSAGES['stop_service'])


if __name__ == '__main__':
    while True:
        main()
        time.sleep(hd.SERVICE_DELAY['one_week'])
