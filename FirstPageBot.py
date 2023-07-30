# -*- coding: utf-8 -*-
import datetime
import sqlite3
import sqlite3 as sql
import statistics
import threading
import time
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
    items_from_buff_old = history[0]
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
        price_buff = convert_price_to_RUB(float(item.get("quick_price")) / 10)
        id_buff = item.get('id')
        buff_link = f'https://buff.163.com/goods/{id_buff}'
        buff_img = item.get('goods_info').get("icon_url")
        price_tm = get_TM_price(item)
        tm_url = f'https://market.csgo.com/ru/'

        if market_hash_name is None or mid_price is None:
            continue
        if int(price_tm) > 15000 or int(count_sell) < 15 or int(price_tm) < 300 or price_buff == 0:
            continue
        profit, profit_middle = check_profit(price_buff, price_tm, mid_price)
        message = f"{market_hash_name}\n" \
                  f"Цена на Buff: {price_buff}\n" \
                  f"Цена на TM(без комиссии): {price_tm}\n" \
                  f"Цена на TM: {price_tm * 0.9}\n" \
                  f"Средняя цена(Без коммиссии): {mid_price}\n" \
                  f"Средняя цена: {mid_price * 0.9}\n" \
                  f"Количество продаж(моя статистика): {count_sell}\n" \
                  f"Ссылка на Buff: {buff_link}\n" \
                  f"ССылка на ТМ: {tm_url}\n" \
                  f"Профит: {round(profit)}%\n" \
                  f"Профит к средней цене: {round(profit_middle)}%"
        print(message)
        if profit > 15 and profit_middle > 15 or profit > 200:
            bot.send_photo(368333609, buff_img, caption=message)
            bot.send_photo(1178860614, buff_img, caption=message)
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
    while True:
        main()
        time.sleep(3)
