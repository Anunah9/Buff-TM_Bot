import os


db_statistic_path = os.path.join(os.path.curdir, '../src', 'db') + os.path.sep
os.remove(db_statistic_path + 'sell_history.db')
os.system('sqlite3 sell_history_for_write.db ".recover" | sqlite3 sell_history.db')
