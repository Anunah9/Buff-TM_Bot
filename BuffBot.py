import datetime
import random
import sqlite3
import threading
import time
import telebot
from pycbrf.toolbox import ExchangeRates
import requests
from os import path
from utils import Database
from urllib.parse import quote
from AutoBuyItems import BuffBuyMethods


def convert_item_name_to_url(name):
    # Используем функцию quote для кодирования имени в URL-формат
    return quote(name)


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


def get_all_items_from_db():
    con = sqlite3.connect(db_statistic_path + 'buff_db.db')
    cur = con.cursor()
    items = cur.execute('SELECT * FROM items')
    items = items.fetchall()
    return items


def catch_data_from_buff(goods_id):  # Разбить на две функции получения цены и картинки
    url = 'https://buff.163.com/api/market/goods/sell_order?game=csgo&goods_id=' + str(goods_id)
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                                                        '(KHTML, like Gecko) Chrome/112.0.0.0 YaBrowser/23.5.2.625 '
                                                        'Yowser/2.5 Safari/537.36'})
    while str(response) != '<Response [200]>':
        print(response)
        time.sleep(5)
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                                            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 '
                                                            'YaBrowser/23.5.2.625 Yowser/2.5 Safari/537.36'})
    return response.json()


def get_price_buff(data_from_buff):
    today = str(datetime.datetime.today().date())
    exchange_rate = float(ExchangeRates(today)['CNY'].value)
    return float(data_from_buff.get('data').get('items')[0].get('price')) * exchange_rate


def get_img_item_from_buff(data_from_buff):
    return data_from_buff.get('data').get('items')[0].get('asset_info').get('info').get('icon_url')


def get_price_history_tm(market_hash_name):
    print(market_hash_name)
    url = f'https://market.csgo.com/api/v2/get-list-items-info?key={API_TM}&list_hash_name[]={market_hash_name}'
    response = requests.get(url)
    data = response.json()['data'][market_hash_name]
    min_price = data['min']
    max_price = data['max']
    avg_price = data['average']
    return avg_price


def main(item):
    global check  # Cостояние обновления бд ТМ
    while check != 0:
        time.sleep(5)
    market_hash_name, buff_link, goods_id = item
    try:
        price_tm, _ = db_TM.get_min_price(market_hash_name)
    except TypeError:
        return False
    price_tm = price_tm / 100
    if price_tm < min_limit_price or max_limit_price < price_tm:
        return False
    price_history = Database.PriceHistory(market_hash_name, db_statistic_path + 'sell_history.db', 7)
    if len(price_history.price_history) <= 1:
        return False
    price_history.delete_anomalies()

    avg_price, count_sell = price_history.get_middle_price_and_count()
    if count_sell < min_limit_count:
        return False

    volatility = price_history.get_price_volatility()

    if not volatility:
        volatility_value = 0
    else:
        volatility_value = sum(volatility)

    print("Волатильность", volatility_value)
    if volatility_value < min_volatility:
        return False
    data_from_buff = catch_data_from_buff(goods_id)
    buff_img = get_img_item_from_buff(data_from_buff)

    price_buff = get_price_buff(data_from_buff)
    fee = 0.9
    price_tm_fee = price_tm * fee
    avg_price_fee = avg_price * fee

    profit = ((price_tm_fee / price_buff) - 1) * 100
    profit_middle = ((avg_price_fee / price_buff) - 1) * 100

    # tm_url = f'https://market-old.csgo.com/item/{class_id}-{instance_id}'
    tm_url = f'https://market.csgo.com/ru/{convert_item_name_to_url(market_hash_name)}'
    message = f"{market_hash_name}" \
              f"\nЦена на Buff: {price_buff}" \
              f"\nЦена на TM(без комиссии): {price_tm}" \
              f"\nЦена на TM: {price_tm_fee}" \
              f"\nСредняя цена: {avg_price}" \
              f"\nСредняя цена(Без комиссии): {avg_price_fee}" \
              f"\nКоличество продаж(моя статистика): {count_sell}" \
              f"\nВолатильность: {volatility_value}" \
              f"\nСсылка на Buff: {buff_link}" \
              f"\nСcылка на ТМ: {tm_url}" \
              f"\nПрофит: {round(profit)}%" \
              f"\nПрофит к средней цене: {round(profit_middle)}%"

    if profit < min_profit or profit_middle < min_profit:
        return False
    print(message)
    bot.send_photo(368333609, buff_img, caption=message)
    buff_acc.buy_first_item(buff_link)
    buff_acc.already_buy += price_buff

    # bot.send_photo(1178860614, buff_img, caption=message)
    while check != 0:
        time.sleep(5)
    time.sleep(random.randint(0, 10) / 10)


if __name__ == '__main__':
    bot = telebot.TeleBot('5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA')
    API_TM = 'JRurnjDqe7ioMAk6pEJNbO9v5znx8BN'
    check = 0  # Нужен чтобы при обновлении бд ТМ останавливало выполнение скрипта
    start_first_timer()  # Запускает механизм обновления базы данных
    db_statistic_path = path.join(path.curdir, 'src', 'db') + path.sep
    items_from_db = get_all_items_from_db()  # Достает все предметы из бд buff
    db_TM = Database.DatabaseTM()  # Обновляет базу данных ТМ при первом запуске
    db_TM.full_update_db()

    buff_acc = BuffBuyMethods()

    buff_acc.balance = 5000
    buff_acc.already_buy = 0

    max_limit_price = 600
    min_limit_price = 200
    min_limit_count = 30
    min_volatility = 4
    min_profit = 12
    balance_commission = 0.03  # Процент денег потерянных при пополнении баланса

    start = 0

    k = start  # Номер предмета в бд
    try:
        for i in items_from_db[start::]:
            print(f'Предмет {k} из {len(items_from_db)}')
            k += 1
            if buff_acc.already_buy >= buff_acc.balance:
                bot.send_message(368333609, f'Закупился на {buff_acc.already_buy}')
                break

            if not main(i):
                continue
    except Exception as exc:
        raise Exception
    finally:
        buff_acc.driver.close()
        buff_acc.driver.quit()


