# === 필요한 라이브러리 불러오기 ===
import ee  # Google Earth Engine 파이썬 API
import requests  # 웹 요청 (썸네일 이미지 다운로드)
import pandas as pd
from PIL import Image  # 이미지 파일 열고 저장
from io import BytesIO  # 이미지 바이트 데이터를 PIL로 읽기 위한 버퍼
from datetime import datetime, timedelta, date  # 날짜 처리용
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from dotenv import load_dotenv
import os 

import logging
from logging.handlers import RotatingFileHandler
from script.db import fetch_contract_dat_lon_lat

def get_satellite_image():    


    # === 환경 변수 로드 ===
    load_dotenv()
    project = os.getenv("PROJECT")

    # === 경로 설정 ===
    #DATA_PATH = 'data/interim/apt/apt_with_long_lat.csv'

    SAVE_PATH = 'data/raw/apt_images/'
    LOG_PATH = "data/log/image_download/image_download.log"

    # === 경로 보장 ===
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    os.makedirs(SAVE_PATH, exist_ok=True)

    # === 로거 설정 ===
    LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)
    file_handler = RotatingFileHandler(LOG_PATH, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 콘솔 출력도 원하면 주석 해제
    # stream_handler = logging.StreamHandler()
    # stream_handler.setFormatter(formatter)
    # logger.addHandler(stream_handler)

    # === 병렬처리 설정 ===
    MAX_WORKERS = 30

    # === 데이터 불러오기 ===
    #df = pd.read_csv(DATA_PATH)
    df = fetch_contract_dat_lon_lat()
    df = pd.DataFrame(df)
    df.dropna(inplace=True)
    print(df.head())
    print(df.info())
    #df = df.head(1000) # 테스트용

    # === Earth Engine 초기화 ===
    ee.Authenticate()
    ee.Initialize(project='aptprice-464102')
    print("Google Earth Engine 초기화 완료")

    # === 거래 데이터 리스트화 ===
    apt_transactions = df[['latitude', 'longitude', 'contract_day']].apply(
        lambda row: {
            'lat': row['latitude'],
            'lon': row['longitude'],
            'date': row['contract_day']
        }, axis=1
    ).tolist()
    print("아파트 거래 데이터 정의 완료")

    def process_transaction(idx, tx):
        try:
            lat = tx['lat']
            lon = tx['lon']

            tx_date_raw = tx['date']
            if isinstance(tx_date_raw, date):
                tx_date = datetime.combine(tx_date_raw, datetime.min.time())
            else:
                tx_date = datetime.strptime(tx_date_raw, "%Y-%m-%d")
            # tx_date = datetime.strptime(tx['date'], "%Y-%m-%d")
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
                logger.warning(f"실패: lat={lat}, lon={lon}, idx={idx}, date={tx['date']}, reason=이미지 없음")
                return f"[X] 이미지 없음 (index {idx}): 날짜={tx['date']}"

            image = (
                collection
                .sort('system:time_start', False)
                .first()
            )

            stats = image.reduceRegion(
                reducer=ee.Reducer.percentile([2, 98]),
                geometry=roi,
                scale=10,
                maxPixels=1e8
            ).getInfo()

            if not stats:
                logger.warning(f"실패: lat={lat}, lon={lon}, idx={idx}, date={tx['date']}, reason=통계 없음")
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
                logger.warning(f"실패: lat={lat}, lon={lon}, idx={idx}, date={tx['date']}, reason=URL 생성 실패")
                return f"[X] URL 생성 실패 (index {idx})"

            response = requests.get(url)
            if response.status_code != 200:
                logger.warning(f"실패: lat={lat}, lon={lon}, idx={idx}, date={tx['date']}, reason=이미지 요청 실패, 상태코드={response.status_code}")
                return f"[X] 이미지 요청 실패 (index {idx}): 상태코드 {response.status_code}"

            img = Image.open(BytesIO(response.content))
            img.save(f"{SAVE_PATH}apt_image_{idx}.jpg")
            return  # 성공 시 출력 안함

        except Exception as e:
            logger.warning(f"실패: lat={lat}, lon={lon}, idx={idx}, date={tx['date']}, reason=예외 발생: {e}")
            return f"[X] 예외 발생 (index {idx}): {e}"

    # === 병렬 처리 실행 ===
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_transaction, idx, tx) for idx, tx in enumerate(apt_transactions)]
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            if result:
                print(result)