from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import re
import csv

def crawling_dong_a(MAX_PAGE):

    DRIVER_PATH = 'chromedriver-mac-arm64/chromedriver'

    # Headless 모드 설정
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # 드라이버 경로 설정
    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    # 첫 페이지 열기
    driver.get("https://www.donga.com/news/Economy/RE")

    # 로딩 대기
    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((
        By.CSS_SELECTOR,
        '#contents > div > div > div.divide_area > section > ul > li:nth-child(1) > article > div > h4 > a'
    )))

    # 기준 날짜 설정 (2020년 9월 1일)
    cutoff_date = 20200901

    # 최대 페이지 수
    #MAX_PAGE = 1
    article_links = set()

    for page in range(1, MAX_PAGE + 1):
        offset = (page - 1) * 20 + 1
        url = f"https://www.donga.com/news/Economy/RE?p={offset}&prod=news&ymd=&m="

        try:
            driver.get(url)
            print(f"[INFO] Visiting page {page} -> {url}")
            time.sleep(2)

            links = driver.find_elements(By.CSS_SELECTOR, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and "https://www.donga.com/news/Economy/article/all/" in href:
                    # 날짜 추출 (정규표현식 사용)
                    match = re.search(r'/all/(\d{8})/', href)
                    if match:
                        article_date = int(match.group(1))
                        if article_date >= cutoff_date:
                            article_links.add(href)
        except Exception as e:
            print(f"[ERROR] Failed to process page {page}: {e}")

    # 결과 출력
    print(f"\n✅ 수집된 기사 링크 수 (2020년 9월 1일 이후): {len(article_links)}")
    for link in sorted(article_links):
        print(link)

    driver.quit()

    article_links = list(article_links)

    # Headless 모드 설정
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')


    # 드라이버 경로 설정
    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    article = {}

    for i, url in enumerate(article_links):
        print(f"\n[INFO] ({i+1}/{len(article_links)}) URL 접속 중: {url}")
        try:
            driver.get(url)
            time.sleep(2)  # JS 렌더링 대기

            try:
                # section.news_view 요소 찾기
                section = driver.find_element(By.CSS_SELECTOR, 'section.news_view')

                # 광고, script, iframe 등 불필요 태그 제거
                driver.execute_script("""
                    const section = arguments[0];
                    const tags = section.querySelectorAll('script, style, iframe, div.a1, div.view_ad06, div.view_m_adA, div.view_m_adB');
                    tags.forEach(tag => tag.remove());
                """, section)

                # innerText로 텍스트 추출
                full_text = section.get_attribute('innerText').strip()

                if not full_text:
                    full_text = "본문 없음 (빈 본문)"
                    print(f"[WARNING] 본문이 비어 있음")
                else:
                    print(f"[DEBUG] 본문 추출 성공 ({len(full_text)}자)")

            except Exception as e:
                full_text = '본문 없음'
                print(f"[WARNING] 본문 추출 실패: {e}")

            # 저장
            article[url] = {
                'content': full_text
            }

        except Exception as e:
            print(f"[ERROR] URL 접근 실패: {url} | 에러: {e}")
            article[url] = {
                'content': '접근 실패'
            }

    # 드라이버 종료
    driver.quit()
    print("\n[INFO] 크롤링 완료.")

        # 크롤링 내용 csv로 저장

    with open('data/raw/news/dong_a_ilbo.csv', 'w', newline="", encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['URL', 'content'])

        for url, content in article.items():
            writer.writerow([url, content])
        