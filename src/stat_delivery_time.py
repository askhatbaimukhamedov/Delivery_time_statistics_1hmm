import numpy as np
import pandas as pd
import headers as hd
import requests


class StatDeliveryTime(object):
    """ Класс реализует основные методы для расчета статистики
        по срокам доставок от производителей до складов компании
        а также перемещения между складами компании
    """

    def __init__(self):
        self._headers = {
            'Content-type': 'application/json',
        }
        self.list_to_drop = [
            'warehouse_id', 'item_id', 'fabricator_id', 'item_id',
            'item_guid', 'item_charac_id', 'item_charac_guid'
        ]

    def __send_statistics(self):
        response = requests.get(
            hd.URL['url_stat_to_1hmm'],
            data=open(hd.PATH_DATA['statistics.json'], 'rb'),
            headers=self._headers
        )
        if response.ok:
            print(hd.LOG_MESSAGES['send_statistics'])

    @staticmethod
    def __percentile(per_value):
        def percentile_(delivery_time):
            return np.percentile(delivery_time, per_value)
        percentile_.__name__ = 'percentile_%s' % per_value
        return percentile_

    @staticmethod
    def __pick_days(deliv_time):
        lst = []
        for item in deliv_time.difference:
            lst.append(item.days)
        deliv_time['delivery'] = lst

    @staticmethod
    def __object_to_date(deliv_time, deliv_time_features, name_features):
        deliv_time[name_features] = pd.to_datetime(
            deliv_time_features,
            format=hd.DATE_FORMAT['from_service']
        )

    @staticmethod
    def __make_offer(delivery_time):
        delivery_time['Offer'] = delivery_time[
            ['item_guid', 'item_charac_guid']
        ].apply(lambda x: '#'.join(x), axis=1)

    @staticmethod
    def __rename_drop_deliv(data_frame, str_feature):
        data_frame[str_feature] = data_frame.delivery
        data_frame.drop('delivery', axis=1, inplace=True)

    def __eval_statistics(self, delivery_time, list_by_group):
        deliv_min = delivery_time.groupby(list_by_group).agg(
            {'delivery': self.__percentile(50)}
        ).reset_index()

        deliv_max = delivery_time.groupby(list_by_group).agg(
            {'delivery': self.__percentile(90)}
        ).reset_index()

        self.__rename_drop_deliv(deliv_max, 'DaysTo')
        self.__rename_drop_deliv(deliv_min, 'DaysFrom')

        if 'Offer' not in list_by_group:
            deliv_max['Offer'] = pd.Series(
                ['' for _ in range(len(deliv_max.index))]
            )
        return pd.merge(
            deliv_max, deliv_min,
            on=list_by_group,
            how='left'
        )

    def get_statistics(self, delivery_time):
        self.__make_offer(delivery_time)
        delivery_time.drop(self.list_to_drop, axis=1, inplace=True)
        delivery_time.rename(
            columns={
                'warehouse_guid': 'PlacementToId',
                'fabricator_guid': 'PlacementFromId'
            }, inplace=True
        )

        # Предварительная подготовка датасета для расчета статистики
        self.__object_to_date(delivery_time, delivery_time.date_receipt, 'date_receipt')
        self.__object_to_date(delivery_time, delivery_time.date_orders, 'date_orders')
        delivery_time = delivery_time.sort_values(by=['date_receipt'])
        delivery_time['difference'] = delivery_time.date_receipt - delivery_time.date_orders
        self.__pick_days(delivery_time)

        # Посчитаем статистику и отправим на сайт 1hmm
        statistics = self.__eval_statistics(
            delivery_time,
            ['PlacementFromId', 'PlacementToId',
             'IsFromSupplier', 'Offer']
        )
        stat_common = self.__eval_statistics(
            delivery_time, ['PlacementFromId', 'PlacementToId', 'IsFromSupplier']
        )

        # Объеденим общие сроки и сроки
        # по товарам и удлим нулевые гуиды
        statistics = statistics.append(stat_common)
        statistics = statistics.loc[
            statistics['PlacementFromId'] != hd.BAD_GUID
        ]

        # Сохраним и отправим на 1hmm посчитанную статистику
        statistics.to_json(hd.PATH_DATA['statistics.json'], orient='records')
        self.__send_statistics()
