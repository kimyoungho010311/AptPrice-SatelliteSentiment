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

    import logging
    from logging.handlers import RotatingFileHandler

    load_dotenv()
    project = os.getenv("PROJECT")

    # === 디렉토리 모음 ===
    # 다운로드한 이미지 저장 디렉토리
    SAVE_PAHT = 'data/raw/apt_images/'
    # 위경도날짜 CSV 디렉토리
    DATA_PATH = 'data/interim/apt/apt_with_long_lat.csv'
    # 로그 저장하는 디렉토리
    LOG_PATH = 'data/log/image_download/image_download.log'
    LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            RotatingFileHandler(LOG_PATH, maxBytes=5*1024*1024, backupCount=5), # 5MB 단위로 로그 작성 데이터를 교환
            #logging.StreamHandler() #콘솔에도 출력되고 로그기록에도 남기고싶으면 주석 해제
        ]
    )

    MAX_WORKERS = 30 # 병렬처리할때 사용할 일꾼

    df = pd.read_csv(DATA_PATH)
    df.dropna(inplace=True)

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
    print("아파트 거래 데이터 정의 완료")

    # -----------------------------------------------------------
    # 1. Google Earth Engine 초기화
    # -----------------------------------------------------------
    ee.Authenticate()
    ee.Initialize(project='aptprice-464102')
    print("Google Earth Engine 초기화 완료")
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
    print("아파트 거래 데이터 정의 완료")

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
                logging.warning(f"실패: lat={lat}, lon={lon}, idx={idx}, date={tx['date']}, reason=이미지 없음")
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
                logging.warning(f"실패: lat={lat}, lon={lon}, idx={idx}, date={tx['date']}, reason=통계 없음")
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
                logging.warning(f"실패: lat={lat}, lon={lon}, idx={idx}, date={tx['date']}, reason=URL 생성 실패 (index {idx})")
                return f"[X] URL 생성 실패 (index {idx})"

            response = requests.get(url)
            if response.status_code != 200:
                logging.warning(f"실패: lat={lat}, lon={lon}, idx={idx}, date={tx['date']}, reason=URL 생성 실패 (index {idx})")
                return f"[X] 이미지 요청 실패 (index {idx}): 상태코드 {response.status_code}"

            img = Image.open(BytesIO(response.content))
            img.save(f"{SAVE_PAHT}apt_image_{idx}.jpg")
            return# f"[✓] 이미지 저장 완료: apt_image_{idx}.jpg"

        except Exception as e:
            logging.warning(f"실패: lat={lat}, lon={lon}, idx={idx}, date={tx['date']}, reason=예외 발생 (index {idx}): {e}")
            return f"[X] 예외 발생 (index {idx}): {e}"

    os.makedirs("data/error_logs/", exist_ok=True)

    # 에러 로그 CSV로 저장

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_transaction, idx, tx) for idx, tx in enumerate(apt_transactions)]
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            if result:  # 실패한 경우만 출력
                print(result)