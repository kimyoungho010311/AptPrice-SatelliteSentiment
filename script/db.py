import pymysql
import pandas as pd
def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='As589788@@',
        db='apt_price',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def load_urls_from_db():
    db_urls = []
    try:
        conn = get_connection()
        
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
        conn = get_connection()

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

def create_raw_sale_table():
    """
    원본 아파트 매매 데이터를 저장하는 테이블을 만듭니다.
    """
    try:
        conn = get_connection()

        cursor = conn.cursor()
        sql = """
            CREATE TABLE IF NOT EXISTS apt_raw_sales (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                region VARCHAR(50) NOT NULL,              -- 시군구
                lot_number VARCHAR(20) NOT NULL,          -- 번지
                main_number INT NOT NULL,                 -- 본번
                sub_number INT NOT NULL,                  -- 부번
                complex_name VARCHAR(100) NOT NULL,       -- 단지명
                area_m2 FLOAT NOT NULL,                   -- 전용면적(㎡)
                contract_ym INT NOT NULL,                 -- 계약년월
                contract_day INT NOT NULL,                -- 계약일
                price_str VARCHAR(20) NOT NULL,           -- 거래금액(만원), 쉼표 포함되어 있음
                building_name VARCHAR(20),                -- 동 NULL 허용
                floor INT,                                -- 층
                buyer VARCHAR(50),                        -- 매수자
                seller VARCHAR(50),                       -- 매도자
                built_year INT,                           -- 건축년도
                street_name VARCHAR(100),                 -- 도로명
                cancel_date VARCHAR(20),                  -- 해제사유발생일
                deal_type VARCHAR(50),                    -- 거래유형
                agency_location VARCHAR(100),             -- 중개사소재지
                registration_date VARCHAR(20)             -- 등기일자
            ) CHARACTER SET utf8mb4;
"""     
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"apt_raw_sales 테이블 생성 완료")
    except Exception as e:
        print(f"apt_raw_sales 테이블 생성 오류 : {e}")

def create_interim_apt_sale():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
        CREATE TABLE IF NOT EXISTS interim_apr_sale (
            area_m2 DOUBLE NOT NULL,
            complex_name VARCHAR(255) NOT NULL,
            floor INT NOT NULL,
            contract_day DATE NOT NULL,
            street_name VARCHAR(255) NOT NULL,
            built_year INT NOT NULL,
            price_per_m2 DOUBLE NOT NULL,
            apartment_age INT NOT NULL,
            alpha DOUBLE NOT NULL
        );
        """
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        print("Interim apt sale 테이블 생성 완료!")

    except Exception as e:
        print(f"Interim apt sale 테이블 생성 실패 : {e}")


def fetch_all_apt_raw_sale():
    """
    apt_raw_sale 테이블에서 모든 정보를 가져옵니다.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            SELECT 
                region,area_m2,contract_ym,complex_name,
                floor,building_name,price_str,contract_day,
                street_name,built_year
            FROM apt_price.apt_raw_sales;
            """

        cursor.execute(sql)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return rows
    except Exception as e:
        print(f"apt_raw_sale 데이터 조회 오류 : {e}")
        return []

def insert_into_interim_apt_sale(df):

    try:
        conn = get_connection()
        cursor = conn.cursor()

        insert_sql = """
        INSERT INTO interim_apr_sale (
            area_m2, complex_name, floor, contract_day,
            street_name, built_year, price_per_m2,
            apartment_age, alpha
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        data = [
            (
                float(row['area_m2']),
                str(row['complex_name']),
                int(row['floor']),
                row['contract_day'].date() if isinstance(row['contract_day'], pd.Timestamp) else pd.to_datetime(row['contract_day']).date(),
                str(row['street_name']),
                int(row['built_year']),
                float(row['price_per_m2']),
                int(row['apartment_age']),
                float(row['alpha'])
            )
            for _, row in df.iterrows()
        ]

        cursor.executemany(insert_sql, data)
        conn.commit()
        cursor.close()
        conn.close()
        print("Data inserted into interim_apr_sale successfully.")

    except Exception as e:
        print(f"Insert failed: {e}")


# def insert_raw_data_to_apt_sales() :


#     """
#     미완성임 쓰면 ㅈ댐
#     """

#     import pandas as pd
#     import pymysql

#     def get_connection():
#         return pymysql.connect(
#             host='localhost',
#             user='root',
#             password='As589788@@',
#             db='apt_price',
#             charset='utf8mb4',
#             cursorclass=pymysql.cursors.DictCursor
#         )

#     # CSV 읽기
#     df = merged_df

#     # 데이터 전처리 (예: 거래금액 쉼표 제거)
#     df['거래금액(만원)'] = df['거래금액(만원)'].str.replace(',', '').astype(str)

#     # NULL 허용 컬럼의 '-' 처리 (예: '동', '매수자' 등)
#     df.replace('-', None, inplace=True)

#     # 컬럼명 영문 매핑
#     df = df.rename(columns={
#         '시군구': 'region',
#         '번지': 'lot_number',
#         '본번': 'main_number',
#         '부번': 'sub_number',
#         '단지명': 'complex_name',
#         '전용면적(㎡)': 'area_m2',
#         '계약년월': 'contract_ym',
#         '계약일': 'contract_day',
#         '거래금액(만원)': 'price_str',
#         '동': 'building_name',
#         '층': 'floor',
#         '매수자': 'buyer',
#         '매도자': 'seller',
#         '건축년도': 'built_year',
#         '도로명': 'street_name',
#         '해제사유발생일': 'cancel_date',
#         '거래유형': 'deal_type',
#         '중개사소재지': 'agency_location',
#         '등기일자': 'registration_date'
#     })

#     # DB 삽입
#     conn = get_connection()
#     cursor = conn.cursor()

#     sql = """
#     INSERT INTO apt_raw_sales (
#         region, lot_number, main_number, sub_number, complex_name, area_m2,
#         contract_ym, contract_day, price_str, building_name, floor, buyer,
#         seller, built_year, street_name, cancel_date, deal_type, agency_location, registration_date
#     ) VALUES (
#         %s, %s, %s, %s, %s, %s,
#         %s, %s, %s, %s, %s, %s,
#         %s, %s, %s, %s, %s, %s, %s
#     )
#     """

#     data_tuples = [tuple(row) for row in df.to_numpy()]

#     try:
#         cursor.executemany(sql, data_tuples)
#         conn.commit()
#     finally:
#         cursor.close()
#         conn.close()