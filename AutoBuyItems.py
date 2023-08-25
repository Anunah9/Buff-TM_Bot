import pickle
import time
import picle
import useragent as useragent
from selenium import webdriver
from selenium.webdriver.common.by import By


class BuffBuyMethods:
    def __init__(self):
        self.chrome_options = webdriver.ChromeOptions()
        self.useragent = f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                         f'Chrome/114.0.0.0 YaBrowser/23.7.3.824 Yowser/2.5 Safari/537.36'
        self.chrome_options.add_argument(self.useragent)  # Исправление: Добавить self.useragent
        self.driver = webdriver.Chrome(options=self.chrome_options)  # Исправление: Передать параметр options
        self.driver.get('https://buff.163.com/market/')
        self.load_cookies()
        self.already_buy = None
        self.balance = None
        time.sleep(3)

    def create_cookie(self):
        self.driver.execute_script('loginModule.steamLogin()')
        print('жду выполнение логина')
        time.sleep(40)
        print('Сохраняю cookie')
        pickle.dump(self.driver.get_cookies(), open('cookies', 'wb'))
        print('Готово')

    def buy_first_item(self, url):
        self.driver.get(url)
        time.sleep(3)
        self.driver.find_element(By.XPATH, '//*[starts-with(@id, "sell_order_")]/td[6]/a').click()
        time.sleep(3)
        self.driver.find_element(By.XPATH, '//*[@id="j_popup_epay"]/div[2]/div[4]/a').click()

    def load_cookies(self):
        for cookie in pickle.load(open("cookies", "rb")):
            self.driver.add_cookie(cookie)
        self.driver.refresh()
        time.sleep(3)


if __name__ == '__main__':
    buff_acc = BuffBuyMethods()





