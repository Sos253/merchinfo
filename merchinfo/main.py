import config
from selenium import webdriver
from time import sleep
from bs4 import BeautifulSoup
import inspect, logging
import sqlite3
from selenium.webdriver.chrome.options import Options

import schedule
from datetime import datetime
from threading import Timer
import time
import os

#log in credentials
email = config.EMAIL
password = config.PASSWORD
url = config.DISCORD_URL

logger = logging.getLogger('root')
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)

def log_in(driver):
    try:
        driver.get('https://members.merchinformer.com/login')
        driver.find_element_by_id('email').send_keys(email)
        driver.find_element_by_id('password').send_keys(password)
        driver.find_element_by_xpath("/html/body/section/div[3]/div[1]/div/div[2]/form/div[3]/div/button").click()
    except Exception as e:
        logging.warning('Something messed up! {}'.format(e))
        driver.quit()
    else:
        print('Logged into MerchInformer! ')

def get_amazon_link(soup_tr):
    for wee in soup_tr.find_all('p'):
         for link in wee.find_all('a'):
             if 'amazon' in link.get('href'):
                return link.get('href')

def get_image_link(soup_tr):
    for wee in soup_tr.find_all('div'):
         for link in wee.find_all('img'):
            return link.get('src')

def get_shirt_name(soup_tr):
    for wee in soup_tr.find_all('p'):
         for link in wee.find_all('a'):
             if 'amazon' in link.get('href'):
                return link.text

def get_data_from_mover_and_shaker(driver):
    try:
        for page_number in range(1, 6):
            driver.get('https://members.merchinformer.com/movers-and-shakers?type=daily&page=' + str(page_number))
            soup = BeautifulSoup(driver.page_source, "lxml")
            all_tr = soup.find_all('tr')
            for tr in all_tr:
                image_link = get_image_link(tr)
                amazon_link = get_amazon_link(tr)
                shirt_name = get_shirt_name(tr)
                if image_link:
                    write_into_db(image_link, amazon_link, shirt_name)
            print('Page ' + str(page_number) + ' was just added to the db! ')
        
        get_tables_from_db()

    except Exception as e:
        logger.debug(e)

def write_into_db(image_link, amazon_link, shirt_name):
    try:
        with sqlite3.connect('./assets/db/example.db') as conn:
            now = datetime.now()
            today = '"{0}-{1}-{2}"'.format(now.month, now.day, now.year)
            conn.execute('INSERT INTO ' + today + ' (shirt_name, amazon_link, image_link) VALUES (?, ?, ?)', (shirt_name, amazon_link, image_link))
            conn.commit()
        conn.close()
    except Exception as e:
        logger.debug(e)

def get_tables_from_db():
    with sqlite3.connect('./assets/db/example.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        result = cur.fetchall()
        print (result)
    conn.close()

def create_todays_table():
    try:
        print ("current path : " + os.getcwd())
        print ("absoulte path: " + os.path.abspath('assets/db/example.db'))
        if os.path.isfile('assets/db/example.db'):
            print ("exists")
        print (os.listdir(os.getcwd()))
        
        with sqlite3.connect('./assets/db/example.db') as conn:
            now = datetime.now()
            today = '{0}-{1}-{2}'.format(now.month, now.day, now.year)
            sql = "create table if not exists '{}' (shirt_name text,amazon_link text,image_link text)".format(today)
            conn.execute(sql)
            conn.commit()
        conn.close()
    except Exception as e:
        logging.warning(e)

def main():
    GOOGLE_CHROME_BIN = "/app/.apt/usr/bin/google-chrome"
    CHROMEDRIVER_PATH = "./chromedriver"
    options = Options()
    options.binary_location = GOOGLE_CHROME_BIN
    options.add_argument('--no-sandbox')
    options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=options)
    try:
        print('starting')
        log_in(driver)
        create_todays_table()
        get_data_from_mover_and_shaker(driver)
        driver.quit()
    except (Exception, KeyboardInterrupt) as e:
        print('error!')
        logging.warning(e)
        driver.quit()

# print ("This script will run at 12:00 everyday")
# # schedule.every(6).seconds.do(main)
# schedule.every().day.at("12.00").do(main)

# while 1:
#     schedule.run_pending()
#     time.sleep(1)

main()
