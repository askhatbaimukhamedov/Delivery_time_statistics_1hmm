import time
import datetime
import data_loader as loader
import stat_delivery_time as deliver
import headers as hd


class PreProcessingError(Exception):
    """ Ошибки возникающие при
        предобработке данных
    """
    def __init__(self, msg):
        self.message = msg


def main():
    ts = time.time()
    data_loader = loader.DataLoader()
    delivery_time = deliver.StatDeliveryTime()

    print(
        hd.LOG_MESSAGES['start_service'],
        datetime.datetime.now(),
        hd.LOG_MESSAGES['separating_line']
    )

    # Загружаем ежедневные исторические данные
    deliv, is_new_data, lst_date = data_loader.load_data()

    if is_new_data:
        # Отправим статистику по срокам доставок
        delivery_time.get_statistics(deliv)

    print(
        hd.LOG_MESSAGES['stop_service'], datetime.datetime.now(),
        hd.LOG_MESSAGES['operating_time'] % ((time.time() - ts) / 60),
        hd.LOG_MESSAGES['separating_line']
    )


if __name__ == '__main__':
    # data_loader = loader.DataLoader()
    # delivery_time = deliver.StatDeliveryTime()
    while True:
        main()
        time.sleep(hd.SERVICE_DELAY['one_week'])
