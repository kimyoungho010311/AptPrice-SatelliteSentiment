import time
import csv
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# 크롬 드라이버 경로
DRIVER_PATH = "/Users/kim-youngho/Desktop/Sellenium/chromedriver-mac-arm64/chromedriver"

# 서울시 25개 자치구 리스트
dvsn_list = [
    '강남구', '강동구', '강북구', '강서구', '관악구',
    '광진구', '구로구', '금천구', '노원구', '도봉구',
    '동대문구', '동작구', '마포구', '서대문구', '서초구',
    '성동구', '성북구', '송파구', '양천구', '영등포구',
    '용산구', '은평구', '종로구', '중구', '중랑구'
]

# 날짜 문자열 정제 함수
def clean_date(raw_date_str):
    if raw_date_str:
        raw_date_str = raw_date_str.replace('입력', '').strip()
        date_part = raw_date_str.split()[0]
        return date_part.rstrip('.')
    return "날짜 없음"

# 본문 정제 함수
def clean_content(raw_content):
    if raw_content:
        return "\n".join([line.strip() for line in raw_content.splitlines() if line.strip()])
    return "본문 없음"

# 셀레니움 설정
options = Options()
options.add_argument("disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_experimental_option("detach", True)

# 25개 자치구 반복
for dvsn in dvsn_list:
    print(f"\n🚩 자치구: {dvsn} 크롤링 시작\n")

    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    driver.get("https://land.naver.com/news/region.naver")
    Select(driver.find_element(By.ID, 'city_no')).select_by_visible_text("서울")
    # time.sleep(1)
    Select(driver.find_element(By.ID, 'dvsn_no')).select_by_visible_text(dvsn)
    # time.sleep(1)

    article_urls = []
    page_limit = 10
    current_page = 1

    while current_page <= page_limit:
        print(f"📄 ({dvsn}) 현재 페이지: {current_page}")
        # time.sleep(1)
        news_links = driver.find_elements(By.CSS_SELECTOR, 'dl > dt:nth-child(2) > a')
        urls = [link.get_attribute('href') for link in news_links if link.get_attribute('href')]
        article_urls.extend(urls)

        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, 'a.next')
            next_btn.click()
            current_page += 1
            # time.sleep(2)
        except NoSuchElementException:
            print("❌ 더 이상 다음 페이지가 없습니다.")
            break

    driver.quit()

    # 중복 제거
    article_urls = list(set(article_urls))
    print(f"✅ 총 수집된 기사 URL 수 ({dvsn}): {len(article_urls)}")

    # 각 기사 내용 크롤링 (날짜 필터링 없음)
    results = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for idx, url in enumerate(article_urls):
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')

            title_tag = soup.select_one('h2#title_area')
            title = title_tag.get_text(strip=True) if title_tag else "제목 없음"

            date_tag = soup.select_one('div.media_end_head_info_datestamp_bunch')
            date_raw = date_tag.get_text(strip=True) if date_tag else None
            date_cleaned = clean_date(date_raw)

            content_tag = soup.select_one('article#dic_area')
            content_raw = content_tag.get_text(separator='\n', strip=True) if content_tag else ""
            content_cleaned = clean_content(content_raw)

            results.append({
                "제목": title,
                "날짜": date_cleaned,
                "본문": content_cleaned,
                "URL": url
            })

            print(f"🔎 [{idx+1}] 수집 완료: {title[:30]}...")

        except Exception as e:
            print(f"⚠️ 오류 발생: {url} / {e}")

    # CSV 저장
    filename = f"../csv/naver/{dvsn}_news.csv"
    with open(filename, "w", newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["제목", "날짜", "본문", "URL"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"✅ CSV 저장 완료: {filename}")