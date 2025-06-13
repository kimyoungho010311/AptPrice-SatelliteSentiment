import time
import csv
import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

DRIVER_PATH = "/Users/kim-youngho/Desktop/Sellenium/chromedriver-mac-arm64/chromedriver"

options = Options()
options.add_argument("disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
options.add_argument("--headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_experimental_option("detach", True)

service = Service(DRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://search.daum.net/search?w=news&q=%EB%B6%80%EB%8F%99%EC%82%B0&enc=utf8&cluster=y&cluster_page=1&DA=PGD&sort=recency&sd=20230121235959&ed=20250101000000&period=u&p=1")
#Select(driver.find_element(By.ID, 'city_no')).select_by_visible_text("서울")

url = "https://search.daum.net/search?w=news&q=%EB%B6%80%EB%8F%99%EC%82%B0&enc=utf8&cluster=y&cluster_page=1&DA=PGD&sort=recency&sd=20230121235959&ed=20250101000000&period=u&p=1"
res = requests.get(url)

time.sleep(5)
driver.quit()

