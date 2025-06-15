def prepro_chosun():
    import pandas as pd
    SAVE_PATH = 'data/interim/news/interim_chosun.csv'

    chosun = pd.read_csv("data/raw/news/chosun_ilbo.csv")

    # 결측 기사는 전부 삭제함
    chosun.dropna(inplace=True)

    # URL 기준으로 날짜 추출함
    chosun['date'] = pd.to_datetime(chosun['URL'].apply(lambda x: "-".join(x.split("/")[5:8])))

    # 날짜 순으로 정렬후 URL 삭제
    chosun.sort_values(by='date',ascending=False, inplace=True)
    chosun.drop('URL', axis=1, inplace=True)
    # 컬럼 순서 변경
    chosun = chosun[['date','content']]
    # 인덱스 번호 초기화
    chosun = chosun.reset_index(drop=True)

    chosun.to_csv(SAVE_PATH, index=False)
    print(f"Interim_chosun_ilbo.csv saved at {SAVE_PATH}")
    
    