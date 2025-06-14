from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)


import csv
import time
import pandas as pd

DRIVER_PATH = 'chromedriver-mac-arm64/chromedriver'

def crawling_chosun(MAX_PAGE):
    """
    사용자가 원하는 페이지 만큼의 뉴스 기사 크롤링

    Args:
        MAX_PAGE (int) : 원하는 페이지 만큼의 기사수를 입력받습니다.

    Returns:
        URL과 해당 뉴스기사의 본문을 'data/raw/news/chosun_ilbo.csv'로 저장합니다.
    """
    #headless mode
    options = Options()
    options.add_argument("--headless")

    # 크롬 드라이버 경로 설정
    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)


    # 웹 페이지 열기
    driver.get("https://www.chosun.com/economy/real_estate/?page=1")

    wait = WebDriverWait(driver, 5)

    anchor = wait.until(EC.presence_of_element_located((
        By.CSS_SELECTOR,
        'div.story-card-component a.story-card__headline'
    )))


    # 최대 몇 번까지 클릭할지 지정
    #MAX_PAGE = 10  # 예: 1~50까지 탐색, MAX_PAGE를 인자값으로 받아오는걸로 수정 (06.14에 수정)
    PAGES_PER_SCREEN = 10

    current = 1
    hrefs = []

    # MAX_PAGE 만큼 뉴스 기사의 URL을 수집하는 while문
    while current <= MAX_PAGE:
        for i in range(current, min(current + PAGES_PER_SCREEN, MAX_PAGE + 1)):
            try:
                # 현재 페이지 범위 내에서 버튼 클릭
                page_button = driver.find_element(By.ID, str(i))
                page_button.click()
                print(f"Clicked page {i}")
                time.sleep(3)
            except NoSuchElementException:
                print(f"[INFO] Page button {i} not found (possibly not visible yet)")
            except Exception as e:
                print(f"Failed to click page {i}: {e}")

        links = driver.find_elements(By.CSS_SELECTOR, "a")
        

        for link in links:
            href = link.get_attribute("href")
            if href:
                hrefs.append(href)


        article_links = [href for href in hrefs if "/economy/real_estate/20" in href]
        
        # 다음 페이지 버튼 클릭 (페이지가 끝나지 않았다면)
        if current + PAGES_PER_SCREEN <= MAX_PAGE:
            try:
                next_page_btn = driver.find_element(
                    By.XPATH,
                    '//*[@id="main"]/div[2]/section/div/div/div/div[21]/div/div[3]/button'
                )
                next_page_btn.click()
                print("Clicked next page button")
                time.sleep(3)
            except Exception as e:
                print(f"Failed to click next page button: {e}")

        # 다음 10개로 이동
        current += PAGES_PER_SCREEN

        driver.quit()

        article_links = set(article_links)
        article_links = list(article_links)

    print("URL crawling is finish.")
    print("Let's crawling content...")


    # 크롬 드라이버 경로 설정
    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    # 기사 본문 수집하는 딕셔너리
    article = {}

    for i in range(len(article_links)):
        # 웹 페이지 열기
        driver.get(article_links[i])
        time.sleep(2)
        try:
            # 기사 본문이 있는 section 선택
            article_section = driver.find_element(By.CSS_SELECTOR, 'section.article-body')
            
            # 모든 <p> 태그에서 텍스트 누적
            full_text = ""
            paragraphs = article_section.find_elements(By.TAG_NAME, 'p')
            
            for p in paragraphs:
                text = p.text.strip()
                if text:
                    full_text += text
        finally:
            # 딕셔너리에 URL을 키로, 본문을 값으로 저장
            article[article_links[i]] = full_text

    driver.quit()
    print("Content crawling is finish.")
    print("Let's save to csv")
    # 크롤링 내용 csv로 저장
    with open('data/raw/news/chosun_ilbo.csv', 'w', newline="", encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['URL', 'content'])

        for url, content in article.items():
            writer.writerow([url, content])

    print("Save csv is finish.")