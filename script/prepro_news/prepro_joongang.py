def prepro_joongang():

    import pandas as pd

    # 중간단계 전처리 기사뉴스 저장되는 경로
    SAVE_PATH = 'data/interim/news/interim_joongang.csv'

    joongang = pd.read_csv('data/raw/news/joongang_ilbo.csv')
    joongang.dropna(inplace=True)
    # 본문 못찾은 기사는 전부 삭제함.
    joongang.drop(["URL"], axis=1,inplace=True)
    joongang['date'] = pd.to_datetime(joongang['date'].str[:10])
    # 날짜순으로 정렬하기
    joongang.sort_values(by='date', ascending=False, inplace=True)
    # 컬럼 순서 변경
    joongang = joongang[['date','content']]
    joongang = joongang.reset_index(drop=True)
    joongang.to_csv(SAVE_PATH, index=False)

    print(f"Interim_jonngang_ilbo.csv saved at {SAVE_PATH}")
