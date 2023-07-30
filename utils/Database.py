import datetime
import os
import statistics
from os import remove
import sqlite3

import numpy as np
import wget
import requests
import pandas as pd


def item_data(func):
    def get_item_statistic(*args):
        self, item_name = args
        query = f"SELECT * FROM test WHERE name = '{item_name}'"
        self.data = self.con.execute(query).fetchall()
        func(*args)

    return get_item_statistic


class Utils:
    @staticmethod
    def convert_time(_time):
        return datetime.datetime.strptime(_time, '%Y-%m-%d %H:%M:%S').date()

    @staticmethod
    def get_date_by_day(days_ago):
        return datetime.datetime.today().date() - datetime.timedelta(days=days_ago)


class PriceHistory:
    def __init__(self, market_hash_name, path_to_statistic_db, days):
        self.path_to_statistic_db = path_to_statistic_db
        self.statistic_db = sqlite3.connect(path_to_statistic_db)
        self.price_history = self.__get_price_history(market_hash_name, days)
        self.days = days

    def __get_price_history(self, market_hash_name, days):
        today = datetime.date.today()
        week_ago = str(today - datetime.timedelta(days=days))
        _time = str(datetime.time(0, 0, 0))
        cur = self.statistic_db.cursor()
        cur.execute(
            f'SELECT price, time FROM history WHERE name = "{market_hash_name}" AND time >= "{week_ago} {_time}"')
        return cur.fetchall()

    def get_middle_price_and_count(self):
        price_history = list(map(lambda x: x[0], self.price_history))
        _middle_price = statistics.mean(price_history)
        count_sell = len(price_history)
        return _middle_price, count_sell

    def find_anomalies(self):
        price_history = list(map(lambda x: x[0], self.price_history))
        anomalies = []
        random_data_std = np.std(price_history)
        random_data_mean = np.mean(price_history)
        anomaly_cut_off = random_data_std * 3
        lower_limit = random_data_mean - anomaly_cut_off
        upper_limit = random_data_mean + anomaly_cut_off
        for outlier in price_history:
            if outlier > upper_limit or outlier < lower_limit:
                anomalies.append(outlier)
        return anomalies

    def delete_anomalies(self):
        anomalies = self.find_anomalies()
        self.price_history = list(filter(lambda x: x[0] not in anomalies, self.price_history))

    def get_sorted_prices_for_day(self, days):
        sorted_price_history = {}
        for day in range(days):
            day = Utils.get_date_by_day(day)
            sorted_price_history[day] = []
        for price in self.price_history:
            now = Utils.convert_time(price[1])
            try:
                sorted_price_history[now].append(price[0])
            except KeyError:
                continue
        sorted_price_history_list = list(sorted_price_history.values())
        return sorted_price_history_list

    def get_price_volatility(self):
        date_lists = self.get_sorted_prices_for_day(self.days)
        median_list = []
        for price in date_lists:
            if len(price) != 0:
                median_list.append(np.median(price))
            else:
                median_list.append(0)
        try:
            volatility = list(map(lambda x: round(((x / median_list[0]) - 1) * 100, 2), median_list))
        except ZeroDivisionError:

            return False
        volatility.pop(0)
        normalized_volatility = []
        for value in volatility:
            if -5 < value < 10:
                normalized_volatility.append(1)
            else:
                normalized_volatility.append(0)
        return normalized_volatility


class DatabaseTM:
    def __init__(self):
        # self.path_to_db = path.join(path.pardir, 'src', 'db') + path.sep
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.db_folder_path = os.path.join(self.current_path, '..', 'src', 'db')
        self.__TM_db_name = self.__get_name_db_csgo_tm__()
        self.con = sqlite3.connect(os.path.join(self.db_folder_path, 'items_on_tm.db'), check_same_thread=False)
        # self.con = sqlite3.connect(self.path_to_db + 'items_on_tm.db', check_same_thread=False)
        self.cur = self.con.cursor()

    @staticmethod
    def __get_name_db_csgo_tm__():
        url = 'https://market.csgo.com/itemdb/current_730.json'
        response = requests.get(url).text.split('"')
        __db_name = response[5]
        return __db_name

    def __get_db_from_csgo_tm__(self):
        url = f'https://market.csgo.com/itemdb/{self.__TM_db_name}'
        wget.download(url, self.db_folder_path)

    def __csv_converter__(self):
        data = pd.read_csv(os.path.join(self.db_folder_path, self.__TM_db_name), index_col=False, sep=";")
        df = pd.DataFrame(data)
        df.head()
        df.pop('c_base_id')
        df.pop('c_rarity')
        df.pop('c_name_color')
        df.pop('c_stickers')
        df.pop('c_slot')
        df.pop('c_offers')
        df.pop('c_price_updated')
        df.pop('c_quality')
        df.pop('c_heroid')
        df.pop('c_pop')

        self.__to_database__(df)

    def __to_database__(self, df):
        try:
            self.cur.execute("""drop table items""")

        except sqlite3.OperationalError:
            print('Таблицы нет')
        df.to_sql('items', self.con)

    def full_update_db(self):
        """На сайте БД обновляется раз в минуту, примерно на 15 секунде минуты"""
        self.__get_db_from_csgo_tm__()
        db_file = os.path.join(self.db_folder_path, self.__TM_db_name)

        self.__csv_converter__()
        remove(db_file)
        print('Готово')

    def get_prices(self, market_hash_name):
        """Возвращает список кортежей типа (price, classid)"""
        query = f'SELECT c_price, c_classid FROM test WHERE c_market_hash_name = "{market_hash_name}"'
        data = self.cur.execute(query)
        data = data.fetchall()
        return data

    def get_min_price(self, market_hash_name):
        """Возвращает кортеж (price, classid) предмета с минимальной ценой"""
        query = f'SELECT c_price, c_classid FROM items WHERE c_market_hash_name = "{market_hash_name}" GROUP BY ' \
                f'c_price'
        min_price = self.cur.execute(query)
        min_price = min_price.fetchone()
        return min_price
