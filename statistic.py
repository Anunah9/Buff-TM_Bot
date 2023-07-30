import datetime
import json
import sqlite3 as sql
import time
import websocket
import logging
from os import path


def convert_time(timestamp):
    return datetime.datetime.fromtimestamp(int(timestamp))


def to_database(name, price, timestamp):
    cur.execute(f"INSERT INTO history VALUES ('{name}', '{convert_time(timestamp)}', '{price}')")
    con.commit()


def on_message(ws, message):
    
    try:
        data = json.loads(json.loads(json.loads(message)['data']))
        if float(data[4]) / 100 > 40:
            print(data[2], float(data[4])/100, convert_time(data[3]))
            to_database(data[2], float(data[4]) / 100, data[3])
    except Exception as exc:
        logging.error(msg=exc)


def on_error(ws, error):
    logging.error(msg=error)
    
    print("received error as {}".format(error))
    return True


def on_close(ws, status, msg):
    logging.error(msg=msg)
    print(status, msg)
    return True


def on_open(ws):
    print("Open connection")
    ws.send('history_go')


def start():
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp("wss://wsnn.dota2.net/wsn/",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                header=header)
    ws.on_open = on_open
    ws.run_forever()


if __name__ == "__main__":
    header = {
        'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0'
    }
    print(path.join(path.curdir, 'src', 'db') + path.sep + 'sell_history.db')
    con = sql.connect(path.join(path.curdir, 'src', 'db') + path.sep + 'sell_history.db')
    cur = con.cursor()
    logging.basicConfig(
        filename="./mylog.log",
        format="%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s"
    )
    
    start()
        

