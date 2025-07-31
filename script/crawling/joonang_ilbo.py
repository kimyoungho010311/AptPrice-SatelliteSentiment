def crawling_joonang(MAX_PAGE):
    # 필요 모듈 import
    from script.db import load_urls_from_db
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
    import csv, time
    import pandas as pd

    DRIVER_PATH = 'chromedriver-mac-arm64/chromedriver'

    # Chrome headless 설정
    options = Options()
    options.add_argument("--headless")
    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    # 초기 페이지 접속
    driver.get("https://www.joongang.co.kr/realestate?page=1")
    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#container > section > div.contents_bottom.float_left > section:nth-child(2) > nav > ul > li.page_next > a')))
    
    #사용자에게 어디까지 크롤링할지 입력받는다.
    #MAX_PAGE = 1
    article_links = []

    # 기사 목록 수집
    for i in range(MAX_PAGE):
        try:
            print(f"{i+1} 번째 페이지 수집 중...")
            time.sleep(2)
            a_tags = driver.find_elements(By.CSS_SELECTOR, '#story_list a')
            for a in a_tags:
                href = a.get_attribute('href')
                if href:
                    article_links.append(href)

            next_page_btn = driver.find_element(By.CSS_SELECTOR, '#container > section > div.contents_bottom.float_left > section:nth-child(2) > nav > ul > li.page_next > a')
            next_page_btn.click()
        except (ElementClickInterceptedException, NoSuchElementException) as e:
            print(f"[예외 발생] 다음 페이지 없음: {e}")
            break

    article_list = list(set(article_links))
    #TODO: DB와 연결해서 중복되는 URL 제거한다.
    db_urls = load_urls_from_db()
    article_links = list(set(article_links) - set(db_urls))  # 차집합으로 필터링
    print(f"\n총 {len(article_list)}개의 기사 링크를 수집했습니다.")

    # 기사 내용 수집
    article_data = {}

    for i, url in enumerate(article_list):
        try:
            driver.get(url)
            print(f"{len(article_list)}개 중 {i+1}번째 기사 크롤링 중...")
            time.sleep(2)

            article_section = driver.find_element(By.CSS_SELECTOR, "#article_body")
            paragraphs = article_section.find_elements(By.TAG_NAME, 'p')
            full_text = ''.join([p.text.strip() for p in paragraphs if p.text.strip()])

            time_element = driver.find_element(By.CSS_SELECTOR, 'time[itemprop="datePublished"]')
            published_date = time_element.get_attribute('datetime')

            article_data[url] = {"text": full_text, "date": published_date}

        except Exception as e:
            print(f"{i+1}번째 기사 오류 발생: {e}")
            continue

    driver.quit()


    # CSV 저장
    
    output_path = 'data/raw/news/joongang_ilbo.csv'
    with open(output_path, 'w', newline="", encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['URL', 'content', 'date'])
        for url, content in article_data.items():
            writer.writerow([url, content["text"], content["date"]])

    print(f" Saved to {output_path}")