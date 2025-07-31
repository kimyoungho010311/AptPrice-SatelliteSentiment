def prepro_chosun():
    from script.db import insert_new_articles_chosun
    import pandas as pd

    chosun = pd.read_csv("data/raw/news/chosun_ilbo.csv")
    chosun.dropna(inplace=True)
    chosun['date'] = pd.to_datetime(chosun['URL'].apply(lambda x: "-".join(x.split("/")[5:8])))
    chosun.sort_values(by='date', ascending=False, inplace=True)
    chosun.drop('URL', axis=1, inplace=True)
    chosun = chosun[['date', 'content']]
    chosun = chosun.reset_index(drop=True)

    url_contents = []
    for idx, row in chosun.iterrows():
        url_contents.append({
            'url': None,
            'content': row['content'],
            'publisher': '조선일보',
            'date': row['date'].to_pydatetime()
        })

    insert_new_articles_chosun(url_contents)