def crawling_chosun(MAX_PAGE):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        NoSuchElementException,
        StaleElementReferenceException,
        TimeoutException,
        WebDriverException,
    )
    import csv, time, os

    DRIVER_PATH = 'chromedriver-mac-arm64/chromedriver'

    options = Options()
    # GUI 없이 실행 - 백엔드/서버 자동화
    options.add_argument("--headless")
    # GPU 가속 기능 off - 안정성 개선
    options.add_argument("--disable-gpu")
    # Chrome을 sandbox 없이 실행함 - 권한 오류 회피(주의)
    options.add_argument("--no-sandbox")

    try:
        service = Service(executable_path=DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 5)
    except WebDriverException as e:
        print(f"[FATAL] Failed to initialize WebDriver: {e}")
        return

    try:
        driver.get("https://www.chosun.com/economy/real_estate/?page=1")
    except Exception as e:
        print(f"[FATAL] Failed to load initial page: {e}")
        driver.quit()
        return

    PAGES_PER_SCREEN = 10
    current = 1
    hrefs = []

    # URL 수집
    while current <= MAX_PAGE:
        for i in range(current, min(current + PAGES_PER_SCREEN, MAX_PAGE + 1)):
            try:
                page_button = driver.find_element(By.ID, str(i))
                page_button.click()
                print(f"[+] Clicked page {i}")
                time.sleep(2)
            except NoSuchElementException: # 지정한 요소를 찾을 수 없을 때 발생
                print(f"[INFO] Page button {i} not found.")
                continue
            except Exception as e:
                print(f"[ERR] Unexpected error clicking page {i}: {e}")
                continue

            try:
                links = driver.find_elements(By.CSS_SELECTOR, "a")
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        if href:
                            hrefs.append(href)
                    except StaleElementReferenceException: # 이미 찾은 웹 요소가 DOM에서 사라져 더 이상 유요하지 못한 경우
                        continue  # 요소가 사라진 경우 무시
            except Exception as e: # 특정 예외 외에도 예상치 못한 모든 예외를 포괄적으로 처리함.
                print(f"[ERR] Failed to extract links on page {i}: {e}")
                continue

        # 다음 페이지 버튼 클릭
        if current + PAGES_PER_SCREEN <= MAX_PAGE:
            try:
                next_page_btn = driver.find_element(
                    By.XPATH,
                    '//*[@id="main"]/div[2]/section/div/div/div/div[21]/div/div[3]/button'
                )
                next_page_btn.click()
                print("[→] Clicked next page button")
                time.sleep(2)
            except NoSuchElementException: # 지정한 요소를 찾을 수 없을 때 발생
                print("[INFO] Next page button not found.")
            except Exception as e: # 지정된 예외 말고도 모든 예외 지정
                print(f"[ERR] Failed to click next page button: {e}")

        current += PAGES_PER_SCREEN

    # 중복 제거
    article_links = list(set([href for href in hrefs if "/economy/real_estate/20" in href]))
    print(f"🔗 Total collected article URLs: {len(article_links)}")

    # 본문 수집
    article = {}
    for i, url in enumerate(article_links):
        try:
            driver.get(url)
            time.sleep(2)
            section = driver.find_element(By.CSS_SELECTOR, 'section.article-body')
            paragraphs = section.find_elements(By.TAG_NAME, 'p')
            full_text = "\n".join(p.text.strip() for p in paragraphs if p.text.strip())
            article[url] = full_text
            print(f"[{i+1}/{len(article_links)}] Crawled: {url}")
        except NoSuchElementException:
            print(f"[ERR] Article structure not found in {url}")
        except TimeoutException: # 페이지 로딩 속도가 너무 느릴 때 발생
            print(f"[ERR] Timeout when loading {url}")
        except Exception as e:
            print(f"[ERR] Failed to crawl content from {url}: {e}")
            continue

    driver.quit()

    # CSV 저장
    output_path = 'data/raw/news/chosun_ilbo.csv'
    try:
        with open(output_path, 'w', newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'content'])
            for url, content in article.items():
                writer.writerow([url, content])
        print(f"✅ Saved to {output_path}")
    except Exception as e:
        print(f"[FATAL] Failed to save CSV: {e}")