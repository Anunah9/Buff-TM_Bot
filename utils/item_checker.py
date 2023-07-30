import datetime
import random
import sqlite3
import statistics
import threading
import time

import numpy as np
import paramiko
import telebot
from pycbrf.toolbox import ExchangeRates
import requests
from fake_useragent import UserAgent

from utils import Database


class Item:
    market_hash_name = ""
    price_BUFF = None

    def __init__(self, _market_hash_name):
        market_hash_name = _market_hash_name



def main_sleep():
    global check
    check = 1
    _dt_now = datetime.datetime.now().second
    _dt_delay = 180 - (_dt_now - 25)
    db_TM.full_update_db()
    threading.Timer(_dt_delay, main_sleep)
    check = 0


def start_first_timer():
    dt_now = datetime.datetime.now().second
    dt_delay = 180 - (dt_now - 25)
    timer = threading.Timer(dt_delay, main_sleep)
    timer.start()


def params():
    _max_limit_price = int(input('Введите максимальную цену: '))
    _min_limit_price = int(input('Введите минимальную цену: '))
    _min_limit_count = int(input('Введите минимальное количество продаж: '))
    _min_profit = int(input('Введите минимальный профит: '))
    return _max_limit_price, _min_limit_price, _min_limit_count, _min_profit


def choose_device(device):
    if device == 'PC':
        db = 'test3.db'
        return db
    else:
        db = '/media/pi/08AD-B26E/TM_Statistic/Code/test1.db'
        return db


def get_all_items_from_db(url):
    con = sqlite3.connect('buff_db.db')
    cur = con.cursor()
    items = cur.execute(f'SELECT * FROM items WHERE url = "{url}" ')
    items = items.fetchone()
    print(items)
    return items


def catch_data_from_buff(goods_id):  # Разбить на две функции получения цены и картинки
    url = 'https://buff.163.com/api/market/goods/sell_order?game=csgo&goods_id=' + str(goods_id)
    response = requests.get(url, headers={'User-Agent': UserAgent().chrome})
    while str(response) != '<Response [200]>':
        print(response)
        time.sleep(5)
        response = requests.get(url, headers={'User-Agent': UserAgent().chrome})
    response = response.json()
    today = str(datetime.datetime.today().date())
    exchange_rate = float(ExchangeRates(today)['CNY'].value)/10
    print("exch", exchange_rate)
    price = float(response.get('data').get('items')[0].get('price')) * exchange_rate
    buff_img = response.get('data').get('items')[0].get('asset_info').get('info').get('icon_url')

    return price, buff_img


def find_anomalies(_data):
    anomalies = []
    random_data_std = np.std(_data)
    random_data_mean = np.mean(_data)
    anomaly_cut_off = random_data_std * 2
    lower_limit = random_data_mean - anomaly_cut_off
    upper_limit = random_data_mean + anomaly_cut_off
    for outlier in _data:
        if outlier > upper_limit or outlier < lower_limit:
            anomalies.append(outlier)

    return anomalies


def middle_price(_name, _price_buff):
    today = datetime.date.today()
    two_week_ago = str(today - datetime.timedelta(days=14))
    _time = str(datetime.time(0, 0, 0))
    cur = db_statistic.cursor()
    cur.execute(f'SELECT price FROM test WHERE name = "{_name}" AND time >= "{two_week_ago} {_time}" AND price >= "{_price_buff}"')
    data_middle_price = cur.fetchall()
    data_middle_price_clean = []
    for price in data_middle_price:
        data_middle_price_clean.append(price[0])
    if len(data_middle_price_clean) <= 1:
        return None, None
    data_middle_price_clean.sort()
    print(data_middle_price_clean)
    anomalies = find_anomalies(data_middle_price_clean)
    print(anomalies)
    for i in data_middle_price_clean:
        if i in anomalies:
            data_middle_price_clean.remove(i)
    if len(data_middle_price_clean) <= 1:
        return None, None
    _middle_price = statistics.mean(data_middle_price_clean)
    count_sell = len(data_middle_price_clean)

    return _middle_price, count_sell


def get_statistic_db_from_server():
    # Open a transport
    host, port = '192.168.1.107', 22
    transport = paramiko.Transport((host, port))
    # Auth
    username = 'pi'
    password = 'raspberry'
    transport.connect(None, username, password)
    # Go!
    sftp = paramiko.SFTPClient.from_transport(transport)
    # Download
    filepath = "/media/pi/08AD-B26E/TM_Statistic/Code/test1.db"
    localpath = "test2.db"
    sftp.get(filepath, localpath)


def main(item):

    global check  # Чекалка состояния обновления бд ТМ
    while check != 0:
        time.sleep(5)

    name, buff_link, goods_id = item

    try:
        price_tm, _ = db_TM.get_min_price(name)
    except TypeError:
        return False
    price_tm = price_tm / 100



    class_id, instance_id = db_TM.con.cursor().execute(f"SELECT c_classid, c_instanceid FROM test WHERE "
                                                       f'c_market_hash_name = "{name}"').fetchone()

    price_buff, buff_img = catch_data_from_buff(goods_id)
    price_tm_fee = price_tm * 0.9
    avg_price, count_sell = middle_price(name, price_buff)
    if avg_price is None or count_sell is None:
        return False
    avg_price_fee = avg_price * 0.9
    profit = ((price_tm_fee/price_buff)-1)*100
    profit_middle = ((avg_price_fee/price_buff)-1)*100

    tm_url = f'https://market.csgo.com/item/{class_id}-{instance_id}'

    message = f"{name}" \
              f"\nЦена на Buff: {price_buff}" \
              f"\nЦена на TM(без комиссии): {price_tm}" \
              f"\nЦена на TM: {price_tm_fee}" \
              f"\nСредняя цена(Без комиссии): {avg_price}" \
              f"\nСредняя цена: {avg_price_fee}" \
              f"\nКоличество продаж(моя статистика): {count_sell}" \
              f"\nСсылка на Buff: {buff_link}" \
              f"\nСcылка на ТМ: {tm_url}" \
              f"\nПрофит: {round(profit)}%" \
              f"\nПрофит к средней цене: {round(profit_middle)}%"

    print(message)
    bot.send_photo(368333609, buff_img, caption=message)
    bot.send_photo(1178860614, buff_img, caption=message)

    while check != 0:
        time.sleep(5)

    time.sleep(random.randint(0, 10)/10)


if __name__ == '__main__':
    bot = telebot.TeleBot('5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA')

    check = 0  # Нужен чтобы при обновлении бд ТМ останавливало выполнение скрипта

    # start_first_timer()  # Запускает механизм обновления базы данных
    items_from_db = get_all_items_from_db('https://buff.163.com/goods/33936')  # Достает все предметы из бд buff

    db_TM = Database.DatabaseTM()  # Обновляет базу данных ТМ при первом запуске
    # db_TM.full_update_db()

    db_statistic_path = choose_device('PC')  # Выбор устройства на котором запущен бот

    db_statistic = sqlite3.connect(db_statistic_path)  # Подключение к бд статистики

    k = 1  # Номер предмета в бд
    if not main(items_from_db):
        print('Что то не так')


