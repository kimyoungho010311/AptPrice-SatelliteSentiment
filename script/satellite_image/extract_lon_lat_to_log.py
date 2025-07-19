def extract_lon_lat_to_log():
    import pandas as pd
    import re

    # 로그 파일 경로
    log_file_path = "data/log/image_download/image_download.log"
    save_path = 'data/log/image_download/log_extract.csv'
    # 로그 파일 읽기
    with open(log_file_path, "r", encoding="utf-8") as f:
        logs = f.read()

    # 정규 표현식 패턴 정의
    pattern = r'lat=([\d.]+), lon=([\d.]+), idx=(\d+), date=([\d\-]+)'

    # 정규 표현식으로 데이터 추출
    matches = re.findall(pattern, logs)

    # DataFrame으로 변환
    df = pd.DataFrame(matches, columns=["위도", "경도", "인덱스", "계약일자"])
    df = df[["경도", "위도", "계약일자", "인덱스"]]
    # CSV 파일로 저장
    df.to_csv(save_path, index=False)
