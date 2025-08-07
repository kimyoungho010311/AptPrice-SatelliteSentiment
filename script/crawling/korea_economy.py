def crawling_korea(MAX_PAGE):
    # 필요 모듈 import
    from script.db import load_urls_from_db
    from selenium import webdriver
    from selenium.webdriver.support.ui import Select
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException
    import csv, time, re
    import pandas as pd
    from datetime import datetime

    # Chrome headless 설정
    options = Options()
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(executable_path='chromedriver-mac-arm64/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 5)


    article_links = []

    def collect_links_from_category(url, category_name):
        driver.get(url)
        for i in range(MAX_PAGE):
            try:
                print(f"[{category_name}] {i+1}번째 페이지 링크 수집중...")

                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#contents > div.select-paging > div.page-select.txt-num > div > select')))
                select_element = driver.find_element(By.CSS_SELECTOR, '#contents > div.select-paging > div.page-select.txt-num > div > select')
                select = Select(select_element)
                select.select_by_value(str(i + 1))
                time.sleep(2)

                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#contents > ul a')))
                a_tags = driver.find_elements(By.CSS_SELECTOR, '#contents > ul a')
                for a in a_tags:
                    href = a.get_attribute('href')
                    if href:
                        article_links.append(href)

            except (NoSuchElementException, StaleElementReferenceException) as e:
                print(f"[예외 발생] 페이지 {i+1} 수집 중 오류: {e}")
                break

    # 카테고리별 수집
    collect_links_from_category('https://www.hankyung.com/economy/economic-policy?page=1', '경제정책')
    collect_links_from_category('https://www.hankyung.com/economy/macro', '거시경제')
    collect_links_from_category('https://www.hankyung.com/economy/forex', '외환시장')
    collect_links_from_category('https://www.hankyung.com/economy/tax', '세금')
    collect_links_from_category('https://www.hankyung.com/economy/job-welfare', '고용복지')

    # 중복 제거
    article_list = list(set(article_links))
    #TODO: DB와 연결해서 중복되는 URL 제거한다.
    db_urls = load_urls_from_db()
    article_links = list(set(article_links) - set(db_urls))  # 차집합으로 필터링

    print(f"\n총 {len(article_list)}개의 기사 링크를 수집했습니다.")

    # 본문 수집
    article = {}

    for i, link in enumerate(article_list):
        driver.get(link)
        time.sleep(2)
        try:
            print(f"{i+1}번째 기사 크롤링 중...")
            article_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#articletxt')))
            article_text = article_element.text.strip()
        except Exception as e:
            print(f"[예외 발생] 기사 본문 수집 실패: {e}")
            article_text = ''
        finally:
            article[link] = article_text

    print(f"총 {len(article)}개의 기사 수집 완료")


    # 크롤링 내용 csv로 저장

    with open('data/raw/news/korea_economy.csv', 'w', newline="", encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['URL', 'content'])

        for url, content in article.items():
            writer.writerow([url, content])
        