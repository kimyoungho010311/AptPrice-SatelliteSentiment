import pymysql

#TODO: DB와 연결해서 중복되는 URL 제거한다.
def load_urls_from_db():
    db_urls = []
    try:
        conn = pymysql.connect(
        host='localhost',
        user='root',
        password='As589788@@',
        db='apt_price',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
        )

        print("새로 발행된 뉴스 기사를 DB에 저장합니다.")
        cursor = conn.cursor()  # 함수 호출 필요
        
        # 2. 쿼리 실행
        query = "SELECT url FROM news"
        cursor.execute(query)

        # 3. 결과 조회
        rows = cursor.fetchall()

        # URL 본문이 저장되는 리스트
        for row in rows:
            db_urls.append(row['url'])
        # print(db_urls)

        # 4. 커서 종료
        cursor.close()
        conn.close()

    except Exception as e:
        print(e)
    return db_urls

def insert_new_articles_chosun(url_contents: list[dict]):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='As589788@@',
            db='apt_price',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        sql = "INSERT INTO news (url, content, publisher, date) VALUES (%s, %s, %s, %s)"
        for item in url_contents:
            cursor.execute(sql, (item['url'], item['content'], item['publisher'], item['date']))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"DB에 새 기사 {len(url_contents)}건 저장 완료")
    except Exception as e:
        print(f"DB 저장 오류: {e}")