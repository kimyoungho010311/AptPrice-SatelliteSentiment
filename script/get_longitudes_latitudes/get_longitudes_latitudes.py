def get_longitudes_latitudes():
    import pandas as pd
    import numpy as np
    import requests
    from tqdm import tqdm
    from dotenv import load_dotenv
    import os
    from pathlib import Path

    load_dotenv()
    api_key = os.getenv("KAKAO_API_KEY")

    OUTPUT_PATH = Path('data/interim/apt/apt_with_long_lat.csv')  
    DF_PATH = Path("data/interim/apt/apt_remove_duplicated.csv")
    # === 데이터 불러오기 === #
    df = pd.read_csv(DF_PATH)
    
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
    for address in tqdm(df['도로명'], desc="좌표 변환 중"):
        x, y = get_coords(address)
        longitudes.append(x)
        latitudes.append(y)

    df['경도'] = longitudes
    df['위도'] = latitudes

    # === 최종 정제 및 저장 === #

    df['면적당 단가(만원)'] = np.log(df['면적당 단가(만원)'])

    # 디렉토리 없으면 생성
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"✅ 저장 완료: {OUTPUT_PATH}")