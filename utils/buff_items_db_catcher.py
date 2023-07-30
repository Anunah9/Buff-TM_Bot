import sqlite3
import time

import requests
from fake_useragent import UserAgent


def catch_data_from_buff(url):
    cookie = {'Locale-Supported': 'en',
              'game': 'csgo',
              'NTES_YD_SESS': 'nEUp64Fvjy5uc0taon9hyaqrXoogE.VOF__bR0tZO29DLUY1xPfMSHEKs_LML7te4sLOzBNUO9xU.7MGtwco.'
                              'nHY7QHpZA4QctuJfpwid_dpBRtRwQmIi1.hGmgB_qJOIoS4v31kvhfodiRYqwOqzP9sglBxTJiaiRqroDVZJjPY'
                              'EXqXxzWxyImwOwuMN6Jov6iZQ4z57YmB.VxBAN.6xELLfAZHf7Cb1EdDwKos.5Fos',
              'S_INFO': '1644676681|0|0&60##|7-9812410499',
              'P_INFO': '7-9812410499|1644676681|1|netease_buff|00&99|null&null&null#RU&null#10#0|&0||7-9812410499',
              'remember_me': 'U1101517572|1Kqt3J6Yh0rQw0qdPnO76wzCkh90E7eF',
              'session': '1-JE34zCzy4SWKQicS7fhFVDdF0lodeCMbikLUWnksCz542036943964',
              'client_id': 'kjTnpsGUKNd2VuQrBS_xuA',
              'csrf_token': 'IjM2YjRkODIzZTUzYzhjMTY5NjdmNWQwZWE0ZDljNDFhMGFlMTk0NmYi.FOlc5g.i6slKU2lx-j10Dqrx-LOI_'
                            '9e4y4'

              }

    response = requests.get(url, headers={'User-Agent': UserAgent().chrome}, cookies=cookie).json()
    print(response)
    items_from_buff = response.get('data').get('items')
    for item in items_from_buff:
        market_hash_name = item.get("market_hash_name")
        id = item.get("id")
        link = f"https://buff.163.com/goods/{id}"
        to_database(market_hash_name, link)


def to_database(name, link):
    con = sqlite3.connect('buff_db.db')
    cur = con.cursor()
    query = f'INSERT INTO items (market_hash_name, url) VALUES ("{name}", "{link}")'
    cur.execute(query)
    con.commit()


def main():
    for page_number in range(1, 911):
        url = f'https://buff.163.com/api/market/goods?game=csgo&page_num={page_number}'
        catch_data_from_buff(url)
        print(f'Страница {page_number} - Готово')
        time.sleep(0.5)


def add_goods_id_to_db(item: tuple):
    item_name, url, _ = item
    print(item_name)
    goods_id = url.split('/')[4]
    con = sqlite3.connect('buff_db.db')
    cur = con.cursor()
    cur.execute('UPDATE items SET goods_id = {} WHERE market_hash_name = "{}"'.format(goods_id, item_name))
    con.commit()


if __name__ == "__main__":
    main()
