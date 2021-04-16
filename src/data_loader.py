import pandas as pd
import json
import requests
import datetime
from datetime import timedelta
import headers as hd
from requests.auth import HTTPBasicAuth


class DataLoader(object):
    """ Класс реализует методы необходимые
        для обновления данных сроков поставок
    """
    def __init__(self):
        self._headers = {
            'Content-type': 'application/json',
        }
        self._data = {
            "НачалоПериода": "date_from",
            "КонецПериода": "date_to",
            "ВидПоставкиТоваров": hd.DELIVERY_TYPE['free_balances']
        }

    def __load_data_from_api(self, service_url):
        response = requests.post(
            service_url,
            auth=HTTPBasicAuth('Web', 'WebMarket'),
            data=json.dumps(self._data),
            headers=self._headers,
            timeout=540
        )
        return response.json()

    @staticmethod
    def __add_is_from_supplier(data_frame, key):
        data_frame['IsFromSupplier'] = pd.Series(
            [key for _ in range(len(data_frame.index))]
        )

    def __load_deliveries(self, delivery_type, supplier):
        self._data["ВидПоставкиТоваров"] = delivery_type
        delivery = pd.DataFrame(
            self.__load_data_from_api(hd.URL['url_del_time'])
        )
        self.__add_is_from_supplier(delivery, supplier)
        return delivery

    @staticmethod
    def __create_cutdate(deliv, deliv_features):
        deliv['cut_date'] = pd.to_datetime(
            deliv_features,
            format=hd.DATE_FORMAT['from_service']
        )

    def __update_date(self, data_frame):
        lst = datetime.datetime.strptime(
            data_frame.values.tolist()[-1][0],
            hd.DATE_FORMAT['from_service']
        )
        self._data["НачалоПериода"] = str(
            datetime.datetime.strftime(
                lst + timedelta(days=1),
                hd.DATE_FORMAT['to_service']
            )
        )
        self._data["КонецПериода"] = str(
            (datetime.date.today() + timedelta(days=1)).strftime(
                hd.DATE_FORMAT['to_service']
            )
        )

    def __update_datasets(self, deliv_old, deliv_new):
        deliv_old.sort_values(by=['date_receipt'], inplace=True)
        deliv_new.sort_values(by=['date_receipt'], inplace=True)

        first_date = datetime.datetime.strptime(
            deliv_old.values.tolist()[0][0],
            hd.DATE_FORMAT['from_service']
        )
        self.__create_cutdate(deliv_old, deliv_old.date_receipt)
        time_peek = first_date + timedelta(weeks=1)
        deliv_old = deliv_old[deliv_old['cut_date'] >= time_peek]
        del deliv_old['cut_date']

        deliv_new = deliv_old.append(deliv_new)
        deliv_new.to_csv(hd.PATH_DATA['delivery_old.csv'], index=False)

        return deliv_new

    def __manual_loading_lost_data(self):
        first = datetime.datetime.strptime(self._data["НачалоПериода"], hd.DATE_FORMAT['to_service'])
        last = datetime.datetime.strptime(self._data["КонецПериода"], hd.DATE_FORMAT['to_service'])

        self._data["НачалоПериода"] = str(
            (first + timedelta(weeks=1)).strftime(hd.DATE_FORMAT['to_service'])
        )

        self._data["КонецПериода"] = str(
            (last + timedelta(weeks=1)).strftime(hd.DATE_FORMAT['to_service'])
        )

    def load_data(self):
        # Заружаем старый датасет со сроками поставок + для графиков на 1hmm
        deliv_old = pd.read_csv(hd.PATH_DATA['delivery_old.csv'], low_memory=False, sep=',')

        # Обновим дату загружаемых данных
        self.__update_date(deliv_old)

        # Раскомментить в случае когда нужно собрать потерянные данные
        # self.__manual_loading_lost_data()

        try:
            # Получаем json-файлы с обовленными данными --> DataFrames
            deliv_sup = self.__load_deliveries(delivery_type=hd.DELIVERY_TYPE['fabricator'], supplier=1)
            deliv_free = self.__load_deliveries(delivery_type=hd.DELIVERY_TYPE['free_balances'], supplier=0)
            deliv_new = deliv_free.append(deliv_sup)

            # Сделаем смещение train_old на train_new
            deliv = self.__update_datasets(deliv_old, deliv_new)

            print(hd.LOG_MESSAGES['successful_download'])
            return deliv, True, self._data["КонецПериода"]

        except ValueError:
            print(hd.LOG_MESSAGES['empty_new_data'])
            return deliv_old, False, self._data["КонецПериода"]
