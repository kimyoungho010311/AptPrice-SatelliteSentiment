import sys
import os

from .satellite_image import get_satellite_image
from .extract_lon_lat_to_log import extract_lon_lat_to_log
from .retry_satellite_image import retry_satellite_image

def combine_satellite():


    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    MAX_RETRY = 5
    cnt = 0
    log_path = 'data/log/image_download/image_download.log'

    # 처음 위성 사진 받기
    get_satellite_image()

    while True:
        # 에러 로그 확인
        with open(log_path, 'r', encoding='utf-8') as f:
            data = f.read().strip()

        if data == "":
            print("====================================")
            print(f"[INFO] All done. Total retry: {cnt}")
            print("====================================")
            break

        if cnt >= MAX_RETRY:
            print(f"[ERROR] Retry limit exceeded ({MAX_RETRY}). Check the issue manually.")
            break

        cnt += 1
        print(f"[INFO] Retry #{cnt} - Errors found in log")

        extract_lon_lat_to_log()

        # 로그 비우기
        open(log_path, 'w').close()

        retry_satellite_image()

