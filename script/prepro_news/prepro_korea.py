def prepro_korea():    
    import pandas as pd
    import re
    from datetime import datetime
    import os

    SAVE_PATH = 'data/raw/news/korea_economy.csv'

    # 데이터 불러오기 및 결측치 제거
    korea = pd.read_csv(SAVE_PATH)
    korea.dropna(inplace=True)

    # 날짜 추출 함수 정의
    def extract_date(url):
        match = re.search(r'/article/(\d{8})', url)
        if match:
            return datetime.strptime(match.group(1), "%Y%m%d").date()
        return None

    # 날짜 컬럼 추가 및 날짜 없는 행 제거
    korea['date'] = korea['URL'].apply(extract_date)
    korea = korea[korea['date'].notnull()]

    # 정렬 및 정리
    korea.sort_values(by='date', ascending=False, inplace=True)
    korea.drop('URL', axis=1, inplace=True)
    korea = korea[['date', 'content']]
    korea.reset_index(drop=True, inplace=True)

    # 저장
    korea.to_csv('data/interim/news/interim_korea_economy.csv', index=False)
    print(f"Interim korea.csv saved at {SAVE_PATH}")
