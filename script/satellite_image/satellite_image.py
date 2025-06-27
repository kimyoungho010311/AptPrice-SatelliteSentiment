def get_satellite_image():    
    # 필요한 라이브러리 불러오기
    import ee  # Google Earth Engine 파이썬 API
    import requests  # 웹 요청 (썸네일 이미지 다운로드에 사용)
    import pandas as pd
    from PIL import Image  # 이미지 파일 열고 저장
    from io import BytesIO  # 이미지 바이트 데이터를 PIL로 읽기 위한 버퍼
    from datetime import datetime, timedelta  # 날짜 처리용
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from tqdm import tqdm
    from dotenv import load_dotenv
    import os 

    load_dotenv()
    project = os.getenv("PROJECT")

    SAVE_PAHT = 'data/raw/apt_images/'
    DATA_PATH = 'data/interim/apt/apt_with_long_lat.csv'

    df = pd.read_csv(DATA_PATH)
    df.dropna(inplace=True)

    error_list = [] # 수집 못한 위도 경도 정보 여기에 저장

    # -----------------------------------------------------------
    # 1. Google Earth Engine 초기화
    # -----------------------------------------------------------
    ee.Authenticate()
    ee.Initialize(project=project)
    print("Google Earth Engine 인증완료")
    # -----------------------------------------------------------
    # 2. 아파트 거래 데이터 정의
    # -----------------------------------------------------------
    apt_transactions = df[['위도', '경도', '계약일자']].apply(
    lambda row: {
        'lat': row['위도'],
        'lon': row['경도'],
        'date': row['계약일자']
    }, axis=1
    ).tolist()

    def process_transaction(idx, tx):
        try:
            lat = tx['lat']
            lon = tx['lon']
            tx_date = datetime.strptime(tx['date'], "%Y-%m-%d")
            start_date = (tx_date - timedelta(days=183)).strftime('%Y-%m-%d')
            end_date = (tx_date + timedelta(days=183)).strftime('%Y-%m-%d')

            center = ee.Geometry.Point([lon, lat])
            roi = center.buffer(1500).bounds()

            collection = (
                ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(center)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5))
            )

            count = collection.size().getInfo()
            if count == 0:
                return f"[X] 이미지 없음 (index {idx}): 날짜={tx['date']}"

            image = (
                collection
                .sort('system:time_start', False) # 최신순 정렬
                .first() # 가장 최근 이미지 선택
            )

            stats = image.reduceRegion(
                reducer=ee.Reducer.percentile([2, 98]),
                geometry=roi,
                scale=10,
                maxPixels=1e8
            ).getInfo()

            if not stats:
                return f"[X] 통계 없음 (index {idx}): 날짜={tx['date']}"

            b4_min = stats.get('B4_p2', 500)
            b4_max = stats.get('B4_p98', 3500)
            b3_min = stats.get('B3_p2', 500)
            b3_max = stats.get('B3_p98', 3500)
            b2_min = stats.get('B2_p2', 500)
            b2_max = stats.get('B2_p98', 3500)

            url = image.getThumbURL({
                'region': roi,
                'format': 'jpg',
                'bands': ['B4', 'B3', 'B2'],
                'min': [b4_min, b3_min, b2_min],
                'max': [b4_max, b3_max, b2_max],
                'scale': 10
            })

            if not url or not url.startswith("https://"):
                return f"[X] URL 생성 실패 (index {idx})"

            response = requests.get(url)
            if response.status_code != 200:
                return f"[X] 이미지 요청 실패 (index {idx}): 상태코드 {response.status_code}"

            img = Image.open(BytesIO(response.content))
            img.save(f"{SAVE_PAHT}apt_image_{idx}.jpg")
            return f"[✓] 이미지 저장 완료: apt_image_{idx}.jpg"

        except Exception as e:
            error_list.append({'lat' : lat, 'lon' : lon, 'datetime' : tx['date']})
            return f"[X] 예외 발생 (index {idx}): {e}"

    os.makedirs("data/error_logs/", exist_ok=True)

    if error_list:
        error_df = pd.DataFrame(error_list)
        error_df.to_csv("data/error_logs/failed_downloads.csv", index=False)
    # 병렬 처리 실행
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_transaction, idx, tx) for idx, tx in enumerate(apt_transactions)]
        for future in tqdm(as_completed(futures), total=len(futures)):
            print(future.result())