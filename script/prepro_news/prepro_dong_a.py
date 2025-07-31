def prepro_dong_a():
    from script.db import insert_new_articles_chosun
    import pandas as pd
    import ast

    SAVE_PATH = 'data/interim/news/interim_dong_a.csv'

    dong_a = pd.read_csv('data/raw/news/dong_a_ilbo.csv')

    dong_a.dropna(inplace=True)
    dong_a['date'] = pd.to_datetime(dong_a["URL"].apply(lambda x: "-".join(x.split("/")[7:8])))
    parsed_dict = ast.literal_eval(dong_a['content'][1])
    cleaned_text = parsed_dict['content'].replace('\\n', ' ')

    # 2. 'content' 문자열을 실제 딕셔너리로 변환 후 \n 제거
    def parse_and_clean(content_str):
        try:
            parsed = ast.literal_eval(content_str)
            return parsed['content'].replace('\\n', ' ').replace('\n', ' ')
        except (ValueError, SyntaxError, KeyError):
            return None  # 오류가 있을 경우 None 반환
    dong_a['content'] = dong_a['content'].apply(parse_and_clean)

    dong_a.drop((['URL']), inplace=True, axis=1)
    dong_a = dong_a[['date','content']]
    dong_a.sort_values(by='date', ascending=False, inplace=True)
    dong_a = dong_a.reset_index(drop=True)

    # dong_a.to_csv(SAVE_PATH, index=False)

    # print(f"Interim_dong_a_ilbo.csv saved at {SAVE_PATH}")
    url_contents = []
    for idx, row in dong_a.iterrows():
        url_contents.append({
            'url': None,
            'content': row['content'],
            'publisher': '동아일보',
            'date': row['date'].to_pydatetime()
        })
    insert_new_articles_chosun(url_contents)