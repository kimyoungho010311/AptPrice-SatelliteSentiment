from script.db import fetch_all_interim_apt_sale, insert_into_lon_lat, create_lon_lat_table
import pandas as pd
import numpy as np
import requests
from tqdm import tqdm
from dotenv import load_dotenv
import os
from pathlib import Path

def get_longitudes_latitudes():

    load_dotenv()
    api_key = os.getenv("KAKAO_API_KEY")

    # === 데이터 불러오기 === #
    df = fetch_all_interim_apt_sale()
    df = pd.DataFrame(df)
    #print(df.head)
    # === 좌표 변환 === #
    headers = {'Authorization': f'KakaoAK {api_key}'}

    def get_coords(address):
        res = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            headers=headers,
            params={'query': address}
        )
        if res.status_code == 200 and res.json()['documents']:
            doc = res.json()['documents'][0]
            return doc['x'], doc['y']
        return None, None

    longitudes, latitudes = [], []
    for address in tqdm(df['street_name'], desc="좌표 변환 중"):
        x, y = get_coords(address)
        longitudes.append(x)
        latitudes.append(y)

    df['longitude'] = longitudes
    df['latitude'] = latitudes

    # === 최종 정제 및 저장 === #

    df['price_per_m2'] = np.log(df['price_per_m2'])

    # 테이블이 없을 시 새로 생성합니다.
    create_lon_lat_table()
    # DB에위도 경도를 삽입합니다.
    insert_into_lon_lat(df)