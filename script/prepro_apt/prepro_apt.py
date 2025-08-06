from script.db import fetch_all_apt_raw_sale, insert_into_interim_apt_sale
def prepro_apt():
    import pandas as pd
    import numpy as np
    from tqdm import tqdm
    import os
    import glob


    # 사용할 컬럼만 지정 (NO 컬럼 제외)
    columns_to_use = [
        'region', 'complex_name', 'area_m2', 'contract_ym', 'contract_day',
        'price_str', 'building_name', 'floor', 'built_year', 'street_name'
    ]

    # apt_raw_sale 테이블에서 원본 아파트 매매 데이터를 불러온다
    rows = fetch_all_apt_raw_sale()   
    df = pd.DataFrame(rows)

    # === 면적당 단가 계산 ===
    df['price_str'] = df['price_str'].str.replace(',', '').astype(int)
    df['price_per_m2'] = df['price_str'] / df['area_m2']

    # === 아파트 나이 계산 ===
    df['contract_year'] = df['contract_ym'].astype(str).str[:4].astype(int)
    df['apartment_age'] = df['contract_year'] - df['built_year']

    # === 거래 날자순으로 나열 === 
    df['contract_day'] = df['contract_ym'].astype(str) + df['contract_day'].astype(str).str.zfill(2)
    df['contract_day'] = pd.to_datetime(df['contract_day'], format='%Y%m%d')
    df = df.sort_values('contract_day').reset_index(drop=True)

    # === 필요 없는 컬럼 삭제 === 
    df.drop(['region','contract_ym','building_name','contract_year'], axis=1, inplace=True)
    
    # =============================================================================
    # 이상치 제거 함수 예시 (IQR 방식 등 사용자 정의 필요)
    def remove_price_outliers(group):
        q1 = group['price_str'].quantile(0.25)
        q3 = group['price_str'].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        filtered = group[(group['price_str'] >= lower) & (group['price_str'] <= upper)]
        return filtered

    def calculate_alpha_from_age_count(age, count, N=30):
        """
        아파트 나이(age)와 해당 월 중복 거래 수(count)를 바탕으로
        대표 거래가 산정을 위한 시계열 가중치 α를 계산한다.

        α = min(1, max(0, (1 - age / N) * log2(count + 1)))

        ▣ α 의미:
        - 월평균 거래가(평균값)와 최신 거래가의 가중 평균에서
            평균값에 부여되는 신뢰도 가중치
        - 0 ≤ α ≤ 1 사이 값

        ▣ 설계 목적:
        - 연식이 오래된 아파트일수록 가격 변동성이 크므로,
            최신 거래가(P_latest)에 더 높은 비중을 부여
        - 거래 수가 많을수록 평균값의 신뢰도는 높아지므로 α 증가

        ▣ 기준 수명 N의 역할:
        - 아파트가 노후되기 시작하는 시점을 수치화 (기본값 30년)
        - 한국 도시정비법상 재건축 가능 기준도 30년 → 현실적 기준
            · age = 0 → α 최대 (평균가 신뢰도 최대)
            · age = N → α = 0 (평균가 신뢰도 제거, 최신값만 사용)

        Parameters:
            age (float): 아파트 나이 (년 단위)
            count (int): 해당 월 중복 거래 수
            N (int): 기준 수명 (default: 30년)

        Returns:
            float: 가중치 α (0 ~ 1 범위)
        """
        raw_alpha = (1 - age / N) * np.log2(count + 1)
        alpha = max(0, min(1, raw_alpha))
        return alpha

    def representative_price(prices, dates, age, N=30):
        """
        월별 이상치 제거된 거래 가격 리스트와 거래일 리스트,
        아파트 나이를 바탕으로 대표 거래가격을 계산한다.

        대표 거래가 = α * 평균 거래가 + (1 - α) * 최신 거래가

        Parameters:
            prices (list or np.ndarray): 이상치 제거 후의 거래 가격 리스트
            dates (list or np.ndarray): 거래일 리스트 (prices와 길이 동일)
            age (float): 아파트 나이
            N (int): 아파트 기준 수명 (기본 30년)

        Returns:
            float or None: 대표 거래 가격. 거래가 없을 경우 None 반환.
        """
        if len(prices) == 0:
            return None  # 거래 없음 → 대표값 계산 불가

        # 가중치 alpha 계산
        count = len(prices)
        alpha = calculate_alpha_from_age_count(age, count, N)

        # 평균 거래가 (P̄)
        avg_price = np.mean(prices)

        # 최신 거래가 (P_latest) → 가장 나중의 날짜 기준
        latest_index = np.argmax(dates)  # 거래일 기준 최대값 인덱스
        latest_price = prices[latest_index]

        # 대표 거래가 계산
        rep_price = alpha * avg_price + (1 - alpha) * latest_price
        return rep_price


    def calculate_alpha_row(group, N=30):
        """
        pandas group (같은 월 내 중복 거래 묶음)을 받아서
        alpha 값을 구하고, 해당 그룹의 첫 row에 붙여 반환.

        Parameters:
            group (pd.DataFrame): 월별 중복 거래 묶음
            N (int): 기준 수명

        Returns:
            pd.DataFrame: alpha가 추가된 대표 row 1개
        """
        age = group['apartment_age'].iloc[0]  # 해당 그룹의 아파트 나이
        count = len(group)  # 그룹 내 거래 수
        alpha = calculate_alpha_from_age_count(age, count, N)

        # 대표 row는 그룹의 첫 row 기준으로 생성
        group = group.sort_values('contract_day')
        row = group.iloc[-1].copy()
        row['alpha'] = alpha

        return pd.DataFrame([row])

        # 1. 이상치 제거
    df_filtered = df.groupby(['street_name', 'complex_name', 'area_m2'], group_keys=False)\
                    .apply(remove_price_outliers)\
                    .reset_index(drop=True)

    # 2. 가중치 α 계산 및 대표 row 추출
    df = df_filtered.groupby(['street_name', 'complex_name', 'area_m2'], group_keys=False)\
                    .apply(calculate_alpha_row)\
                    .reset_index(drop=True)

    df.drop('price_str', axis=1, inplace=True)
    df = df.sort_values('contract_day').reset_index(drop=True)
    print(f"결측치 삭제 전 데이터 길이 : {len(df)}")
    df.dropna(inplace=True)
    print(f"결측치 삭제 후 데이터 길이 : {len(df)}")

    insert_into_interim_apt_sale(df)
    print(f"전처리가 완료되었습니다.")
