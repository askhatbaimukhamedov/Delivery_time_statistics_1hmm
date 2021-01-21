import numpy as np
import pandas as pd
import headers as hd
import datetime
import time
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
        self._list_to_drop_deliv = [
            'warehouse_id', 'item_id', 'fabricator_id',
            'item_guid', 'item_charac_id', 'item_charac_guid'
        ]
        self._list_to_drop_graph = [
            'IsFromSupplier', 'item_id', 'item_guid',
            'item_charac_id', 'item_charac_guid', 'fabricator_id'
        ]

    def __send_statistics(self, servie_url, path_json):
        response = requests.get(
            hd.URL[servie_url],
            data=open(hd.PATH_DATA[path_json], 'rb'),
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

    @staticmethod
    def __common_merge(data_frame_1, data_frame_2):
        return pd.merge(
            data_frame_1, data_frame_2,
            on=['guid_manufactorer', 'warehouseOuterId', 'warehouse_id'],
            how='left'
        )

    @staticmethod
    def __drop_unnecessary(stat):
        stat = stat.loc[stat['PlacementFromId'] != hd.BAD_GUID]
        return stat.loc[
            stat['PlacementFromId'] != stat['PlacementToId']
        ]

    def __prepare_df(self, delivery):
        self.__object_to_date(
            delivery, delivery.date_receipt,
            'date_receipt'
        )
        self.__object_to_date(
            delivery, delivery.date_orders,
            'date_orders'
        )

        delivery['difference'] = delivery.date_receipt - delivery.date_orders
        self.__pick_days(delivery)

        return delivery

    def __eval_percentile(self, delivery, list_by_group, p_min, p_max):
        deliv_min = delivery.groupby(list_by_group).agg(
            {'delivery': self.__percentile(p_min)}
        ).reset_index()

        deliv_max = delivery.groupby(list_by_group).agg(
            {'delivery': self.__percentile(p_max)}
        ).reset_index()

        return deliv_min, deliv_max

    def __get_percentile(self, delivery, list_by_group):
        delivery = delivery.loc[(delivery['delivery'] > 0)]
        deliv_sup = delivery.loc[(delivery['IsFromSupplier'] == 1)]
        deliv_warehouse = delivery.loc[(delivery['IsFromSupplier'] == 0)]

        sup_min, sup_max = self.__eval_percentile(
            deliv_sup, list_by_group,
            hd.PERCENTILE['50percentile'],
            hd.PERCENTILE['90percentile']
        )
        ware_min, ware_max = self.__eval_percentile(
            deliv_warehouse, list_by_group,
            hd.PERCENTILE['30percentile'],
            hd.PERCENTILE['70percentile']
        )
        return sup_min.append(ware_min), sup_max.append(ware_max)

    def __eval_statistics(self, delivery_time, list_by_group):
        deliv_min, deliv_max = self.__get_percentile(
            delivery_time, list_by_group
        )
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
        delivery_time.drop(self._list_to_drop_deliv, axis=1, inplace=True)
        delivery_time.rename(
            columns={
                'warehouse_guid':  'PlacementToId',
                'fabricator_guid': 'PlacementFromId'
            }, inplace=True
        )

        # Предварительная подготовка датасета
        delivery_time = self.__prepare_df(delivery_time)

        # Посчитаем статистику и отправим на сайт 1hmm
        statistics = self.__eval_statistics(
            delivery_time,
            ['PlacementFromId', 'PlacementToId',
             'IsFromSupplier', 'Offer']
        )
        stat_common = self.__eval_statistics(
            delivery_time,
            ['PlacementFromId', 'PlacementToId', 'IsFromSupplier']
        )

        # Подготовим итоговую статистику
        statistics = statistics.append(stat_common)
        statistics = self.__drop_unnecessary(statistics)

        # Сохраним и отправим на 1hmm посчитанную статистику
        statistics.to_json(hd.PATH_DATA['statistics.json'], orient='records')
        self.__send_statistics('url_stat_to_1hmm', 'statistics.json')

    def get_stat_for_graphics(self, delivery, lst_date):
        delivery = delivery.loc[delivery['IsFromSupplier'] == 1]
        delivery.drop(
            self._list_to_drop_graph,
            axis=1, inplace=True
        )
        delivery.rename(
            columns={
                'warehouse_guid':  'warehouseOuterId',
                'fabricator_guid': 'guid_manufactorer'
            }, inplace=True
        )

        # Предварительная подготовка датасета
        delivery = self.__prepare_df(delivery)
        delivery = delivery.loc[delivery['delivery'] > 0]

        # Создадим таблицу со с следующими предикторами
        index_cols = [
            'guid_manufactorer', 'warehouseOuterId',
            'warehouse_id', 'p10Dates', 'highDates', 'lowDates'
        ]

        grid = []

        for fabricator in delivery['guid_manufactorer'].unique():
            cur_fabricator = delivery.loc[delivery['guid_manufactorer'] == fabricator]

            deliv_min = cur_fabricator.groupby(['guid_manufactorer', 'warehouseOuterId', 'warehouse_id']).agg(
                {'delivery': self.__percentile(hd.PERCENTILE['50percentile'])}).reset_index()
            deliv_max = cur_fabricator.groupby(['guid_manufactorer', 'warehouseOuterId', 'warehouse_id']).agg(
                {'delivery': self.__percentile(hd.PERCENTILE['90percentile'])}).reset_index()
            deliv_mean = cur_fabricator.groupby(['guid_manufactorer', 'warehouseOuterId', 'warehouse_id']).agg(
                {'delivery': np.mean}).reset_index()

            self.__rename_drop_deliv(deliv_max, 'highDates')
            self.__rename_drop_deliv(deliv_min, 'p10Dates')
            self.__rename_drop_deliv(deliv_mean, 'lowDates')

            statistics = self.__common_merge(deliv_min, deliv_max)
            statistics = self.__common_merge(statistics, deliv_mean)

            grid.append(statistics)

        stat = pd.DataFrame(np.vstack(grid), columns = index_cols)
        stat['date'] = time.mktime(datetime.datetime.strptime(lst_date, "%d.%m.%Y %H:%M:%S").timetuple()) * 1000

        stat['isArrivalOnly'] = True
        stat['lowDates'] = np.maximum(stat.p10Dates, stat.lowDates)
        stat['highDates'] = np.maximum(stat.highDates, stat.lowDates)

        # Сохраним и отправим на 1hmm посчитанную статистику
        stat.to_json(hd.PATH_DATA['stat_graph.json'], orient='records')
        self.__send_statistics('url_for_graphics', 'stat_graph.json')
