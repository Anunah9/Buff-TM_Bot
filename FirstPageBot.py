# -*- coding: utf-8 -*-
import datetime
import sqlite3 as sql
import statistics
import threading
import time
from os import path
from urllib.parse import quote

from pycbrf.toolbox import ExchangeRates
import numpy as np
import requests
import telebot
from utils import Database

bot = telebot.TeleBot('5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA')


def choose_device(device):
    if device == 'PC':
        db = r'C:\Users\Hanuna\PycharmProjects\TM_Statistic\Code\test1.db'
        return db
    else:
        db = '/media/pi/08AD-B26E/TM_Statistic/Code/test1.db'
        return db


def catch_data_from_buff():
    url = 'https://buff.163.com/api/market/goods?game=csgo&page_num=1 '
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                                                        '(KHTML, like Gecko) Chrome/114.0.0.0 YaBrowser/23.7.1.1140 '
                                                        'Yowser/2.5 Safari/537.36'}).json()
    items_from_buff = response.get('data').get('items')
    return items_from_buff


def buff_data_converter(_data):
    for item in _data:
        [item.pop(key) for key in ['appid', 'bookmarked', 'buy_num', 'can_bargain', 'can_search_by_tournament',
                                   'description', 'game', 'has_buff_price_history', 'market_min_price',
                                   'name', 'sell_num', 'sell_reference_price', 'short_name', 'transacted_num']]
        item.get('goods_info').pop('info')
    return _data


def find_anomalies(_data):
    anomalies = []
    random_data_std = np.std(_data)
    random_data_mean = np.mean(_data)
    anomaly_cut_off = random_data_std * 3
    lower_limit = random_data_mean - anomaly_cut_off
    upper_limit = random_data_mean + anomaly_cut_off
    for outlier in _data:
        if outlier > upper_limit or outlier < lower_limit:
            anomalies.append(outlier)
    return anomalies


def middle_price(_name):
    today = datetime.date.today()
    week_ago = str(today - datetime.timedelta(days=7))
    _time = str(datetime.time(0, 0, 0))
    db = choose_device('PC')
    # db = '/media/pi/08AD-B26E/TM_Statistic/Code/test1.db'
    # db = r'G:\TM_Statistic\Code\test1.db'
    con = sql.connect(db)
    cur = con.cursor()
    cur.execute(f"SELECT price FROM test WHERE name = '{_name}' AND time >= '{week_ago} {_time}'")
    data_middle_price = cur.fetchall()
    data_middle_price_clean = []
    for price in data_middle_price:
        data_middle_price_clean.append(price[0])
    if len(data_middle_price_clean) <= 1:
        return None, None
    anomalies = find_anomalies(data_middle_price_clean)
    for i in data_middle_price_clean:
        if i in anomalies:
            data_middle_price_clean.remove(i)
    if len(data_middle_price_clean) <= 1:
        return None, None
    _middle_price = statistics.mean(data_middle_price_clean)
    count_sell = len(data_middle_price_clean)
    return _middle_price, count_sell


def get_TM_price(market_hash_name):
    return db_TM.get_min_price(market_hash_name)


def convert_item_name_to_url(name):
    # Используем функцию quote для кодирования имени в URL-формат
    return quote(name)


def convert_price_to_RUB(price):
    today = str(datetime.datetime.today().date())
    exchange_rate = float(ExchangeRates(today)['CNY'].value)
    return price * exchange_rate


def check_profit(_price_buff, _price_tm, _middle_price):
    profit = (_price_tm * 0.9 / _price_buff - 1) * 100
    profit_middle = (_middle_price * 0.9 / _price_buff - 1) * 100
    return profit, profit_middle


def main_sleep():
    global check
    check = 1
    _dt_now = datetime.datetime.now().second
    _dt_delay = 180 - (dt_now - 25)
    db_TM.full_update_db()
    threading.Timer(_dt_delay, main_sleep)
    check = 0


def main():
    global check
    items_from_buff_old = history
    print(items_from_buff_old)
    items_from_buff = catch_data_from_buff()
    print(items_from_buff)
    history.clear()
    for item in items_from_buff:
        if item in items_from_buff_old:
            items_from_buff.remove(item)
    for item in items_from_buff:
        if item in items_from_buff_old:
            items_from_buff.remove(item)
    for item in items_from_buff:

        market_hash_name = item['market_hash_name']
        price_buff = convert_price_to_RUB(float(item.get("quick_price")))
        id_buff = item.get('id')
        buff_link = f'https://buff.163.com/goods/{id_buff}'
        buff_img = item.get('goods_info').get("icon_url")

        price_tm = db_TM.get_min_price(market_hash_name)
        if price_tm:
            price_tm = price_tm[0] / 100
        else:
            continue

        if price_tm < min_limit_price or max_limit_price < price_tm:
            continue

        price_history = Database.PriceHistory(market_hash_name, db_statistic_path + 'sell_history.db', 7)

        if len(price_history.price_history) <= 1:
            continue
        price_history.delete_anomalies()

        avg_price, count_sell = price_history.get_middle_price_and_count()
        if count_sell < min_limit_count:
            continue

        volatility = price_history.get_price_volatility()
        if not volatility:
            volatility_value = 0
        else:
            volatility_value = sum(volatility)
        tm_url = f'https://market.csgo.com/ru/{convert_item_name_to_url(market_hash_name)}'

        if market_hash_name is None or avg_price is None:
            continue
        if int(price_tm) > max_limit_price or int(count_sell) < min_limit_count or int(price_tm) < min_limit_price:
            continue
        profit, profit_middle = check_profit(price_buff, price_tm, avg_price)
        # message = f"{market_hash_name}\n" \
        #           f"Цена на Buff: {price_buff}\n" \
        #           f"Цена на TM(без комиссии): {price_tm}\n" \
        #           f"Цена на TM: {price_tm * 0.9}\n" \
        #           f"Средняя цена(Без коммиссии): {avg_price}\n" \
        #           f"Средняя цена: {avg_price * 0.9}\n" \
        #           f"Количество продаж(моя статистика): {count_sell}\n" \
        #           f"Волатильность: {volatility_value}\n" \
        #           f"Ссылка на Buff: {buff_link}\n" \
        #           f"Ссылка на ТМ: {tm_url}\n" \
        #           f"Профит: {round(profit)}%\n" \
        #           f"Профит к средней цене: {round(profit_middle)}%"
        message = f"Название предмета: {market_hash_name}\n" \
                  f"Цены:\n" \
                  f"- Цена на Buff: {price_buff:.2f} (без комиссии)\n" \
                  f"- Цена на ТМ: {price_tm:.2f} (с учетом комиссии)\n" \
                  f"- Средняя цена на TM: {avg_price:.2f} (без комиссии)\n" \
                  f"- Средняя цена на ТМ: {avg_price * 0.9:.2f} (с учетом комиссии)\n" \
                  f"\nСтатистика:\n" \
                  f"- Количество продаж (по вашей статистике): {count_sell}\n" \
                  f"- Волатильность: {volatility_value}\n" \
                  f"\nПрофит:\n" \
                  f"- Профит: {round(profit)}% (разница между покупной и продажной ценами)\n" \
                  f"- Профит к средней цене: {round(profit_middle)}% (разница между покупной и средней ценами)\n" \
                  f"\nСсылки:\n" \
                  f"- Ссылка на Buff: {buff_link}\n" \
                  f"- Ссылка на ТМ: {tm_url}"

        print(message)
        print('--------------------------------------------------')
        if profit > min_profit or profit > 200:
            bot.send_photo(368333609, buff_img, caption=message)
        while check != 0:
            time.sleep(5)
    history.append(items_from_buff)


if __name__ == "__main__":
    check = 0
    db_TM = Database.DatabaseTM()  # Обновляет базу данных ТМ при первом запуске
    db_TM.full_update_db()
    dt_now = datetime.datetime.now().second
    dt_delay = 180 - (dt_now - 25)
    timer = threading.Timer(dt_delay, main_sleep)
    timer.start()
    global items_from_buff_old
    history = [[]]

    db_statistic_path = path.join(path.curdir, 'src', 'db') + path.sep

    max_limit_price = 100000
    min_limit_price = 200
    min_limit_count = 30
    min_volatility = 4
    min_profit = 19

    while True:
        main()
        time.sleep(3)
