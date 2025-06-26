import pandas as pd
import glob
import os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

SEQ_LEN = 12
BATCH_SIZE = 32
EPOCHS = 20
HIDDEN_SIZE = 64
LR = 1e-3

def load_and_preprocess_data(folder_path):
    print("[1/8] 데이터 로딩 및 초기 전처리 시작")
    columns_to_use = [
        '시군구', '번지', '본번', '부번', '단지명', '전용면적(㎡)', '계약년월', '계약일',
        '거래금액(만원)', '동', '층', '매수자', '매도자', '건축년도', '도로명', '해제사유발생일',
        '거래유형', '중개사소재지', '등기일자'
    ]
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    print(f"[1/8] 총 {len(csv_files)}개의 CSV 파일 발견")
    df_list = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, encoding='cp949', skiprows=15, usecols=columns_to_use)
            df_list.append(df)
            print(f"[1/8] {os.path.basename(file)} 파일 로딩 완료: {len(df):,}건")
        except Exception as e:
            print(f"[1/8] {os.path.basename(file)} 파일 로딩 실패: {e}")

    df = pd.concat(df_list, ignore_index=True)
    print(f"[1/8] 모든 파일 병합 완료: 총 {len(df):,}건")

    df['거래금액(만원)'] = df['거래금액(만원)'].str.replace(',', '').astype(int)
    df['면적당 단가(만원)'] = df['거래금액(만원)'] / df['전용면적(㎡)']
    df['계약년도'] = df['계약년월'].astype(str).str[:4].astype(int)
    df['아파트 나이'] = df['계약년도'] - df['건축년도']
    df['구'] = df['시군구'].str.extract(r'(\S+구)')
    drop_cols = [
        '시군구', '번지', '본번', '부번', '동', '층', '매수자', '매도자',
        '계약년도', '구', '해제사유발생일', '거래유형', '중개사소재지', '등기일자',
    ]
    df.drop(drop_cols, axis=1, inplace=True)
    df = df[['전용면적(㎡)','건축년도','아파트 나이','단지명','도로명','면적당 단가(만원)','거래금액(만원)','계약년월','계약일']]
    print(f"[1/8] 불필요 컬럼 제거 및 주요 컬럼 선별 완료, 데이터 shape: {df.shape}")
    return df

def process_group(group):
    if (group['아파트 나이'] <= 10).all():
        row = group.iloc[0].copy()
        row['면적당 단가(만원)'] = group['면적당 단가(만원)'].mean()
        return pd.DataFrame([row])
    else:
        min_age = group['아파트 나이'].min()
        return group[group['아파트 나이'] == min_age].iloc[[0]]

def remove_price_outliers(group):
    q1 = group['거래금액(만원)'].quantile(0.25)
    q3 = group['거래금액(만원)'].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    filtered = group[(group['거래금액(만원)'] >= lower) & (group['거래금액(만원)'] <= upper)]
    print(f"[2/8] 이상치 제거: 그룹 {group.name if hasattr(group, 'name') else ''} 내 {len(group)}건 → {len(filtered)}건")
    return filtered

def sort_by_date(df):
    df = df.copy()
    df['계약일자'] = df['계약년월'].astype(str) + df['계약일'].astype(str).str.zfill(2)
    df['계약일자'] = pd.to_datetime(df['계약일자'], format='%Y%m%d')
    return df.sort_values('계약일자').reset_index(drop=True)

def calculate_alpha_from_age_count(age, count, N=30):
    raw_alpha = (1 - age / N) * np.log2(count + 1)
    alpha = max(0, min(1, raw_alpha))
    return alpha

def calculate_alpha_row(group, N=30):
    age = group['아파트 나이'].iloc[0]
    count = len(group)
    alpha = calculate_alpha_from_age_count(age, count, N)
    row = group.iloc[0].copy()
    row['alpha'] = alpha
    return pd.DataFrame([row])

def prepare_way1(df):
    print("[3/8] Way1: 아파트 나이 기준 그룹 대표가 산정 중...")
    way1 = df.groupby(['도로명','단지명','전용면적(㎡)'], group_keys=False).apply(process_group).reset_index(drop=True)
    way1 = sort_by_date(way1)
    print(f"[3/8] Way1 데이터 개수: {len(way1):,}")
    return way1

def prepare_way2(df):
    print("[4/8] Way2: 이상치 제거 및 alpha 가중치 계산 중...")
    df_filtered = df.groupby(['도로명','단지명','전용면적(㎡)'], group_keys=False)\
                    .apply(remove_price_outliers).reset_index(drop=True)
    way2 = df_filtered.groupby(['도로명','단지명','전용면적(㎡)'], group_keys=False)\
                      .apply(calculate_alpha_row).reset_index(drop=True)
    if '거래금액(만원)' in way2.columns:
        way2.drop('거래금액(만원)', axis=1, inplace=True)
    way2 = sort_by_date(way2)
    print(f"[4/8] Way2 데이터 개수: {len(way2):,}")
    return way2

def prepare_data(df, use_alpha=False):
    print(f"[5/8] 피처 스케일링 시작 (alpha 사용: {use_alpha})")
    target = '면적당 단가(만원)'
    numeric_features = ['전용면적(㎡)', '건축년도', '아파트 나이']
    if use_alpha:
        numeric_features.append('alpha')

    X = df[numeric_features]
    y = df[target].values
    preprocessor = ColumnTransformer([('num', StandardScaler(), numeric_features)])
    X_processed = preprocessor.fit_transform(X)
    print("[5/8] 피처 스케일링 완료")
    return X_processed, y

def train_mlp(X, y):
    print("[6/8] MLP 학습 시작")
    train_size = int(len(X) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    mlp = MLPRegressor(hidden_layer_sizes=(128,64), max_iter=500, random_state=42)
    mlp.fit(X_train, y_train)
    print(f"[6/8] MLP 학습 완료, 학습 데이터: {len(X_train):,}건, 테스트 데이터: {len(X_test):,}건")

    y_pred = mlp.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    print(f"[6/8] MLP 평가 결과 - RMSE: {rmse:.4f}, MAE: {mae:.4f}")
    return rmse, mae

class TimeSeriesDataset(Dataset):
    def __init__(self, X, y, seq_len):
        self.X_seq = []
        self.y_seq = []
        for i in range(len(X) - seq_len):
            self.X_seq.append(X[i:i+seq_len])
            self.y_seq.append(y[i+seq_len])
        self.X_seq = torch.tensor(self.X_seq, dtype=torch.float32)
        self.y_seq = torch.tensor(self.y_seq, dtype=torch.float32)

    def __len__(self):
        return len(self.X_seq)

    def __getitem__(self, idx):
        return self.X_seq[idx], self.y_seq[idx]

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size=HIDDEN_SIZE, num_layers=1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        return self.fc(out).squeeze()

def train_lstm(X, y):
    print("[7/8] LSTM 학습 시작")
    train_size = int(len(X) * 0.8)
    train_dataset = TimeSeriesDataset(X[:train_size], y[:train_size], SEQ_LEN)
    test_dataset = TimeSeriesDataset(X[train_size:], y[train_size:], SEQ_LEN)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    model = LSTMModel(input_size=X.shape[1])
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        for x_batch, y_batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}", leave=False):
            optimizer.zero_grad()
            y_pred = model(x_batch)
            loss = criterion(y_pred, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(train_loader)
        print(f"[7/8] Epoch {epoch+1}/{EPOCHS} - 평균 손실: {avg_loss:.6f}")

    print("[7/8] LSTM 평가 중...")
    model.eval()
    preds, trues = [], []
    with torch.no_grad():
        for x_batch, y_batch in tqdm(test_loader, desc="Evaluating", leave=False):
            y_pred = model(x_batch)
            preds.append(y_pred.cpu().numpy())
            trues.append(y_batch.cpu().numpy())

    preds = np.concatenate(preds)
    trues = np.concatenate(trues)
    rmse = np.sqrt(mean_squared_error(trues, preds))
    mae = mean_absolute_error(trues, preds)
    print(f"[7/8] LSTM 평가 완료 - RMSE: {rmse:.4f}, MAE: {mae:.4f}")
    return rmse, mae

def main(folder_path, use_alpha=False):
    df = load_and_preprocess_data(folder_path)
    way1 = prepare_way1(df)
    way2 = prepare_way2(df)

    if use_alpha:
        X, y = prepare_data(way2, use_alpha=True)
    else:
        X, y = prepare_data(way1, use_alpha=False)

    rmse_mlp, mae_mlp = train_mlp(X, y)
    rmse_lstm, mae_lstm = train_lstm(X, y)

    print(f"[8/8] 최종 결과 - MLP RMSE: {rmse_mlp:.4f}, MAE: {mae_mlp:.4f} | LSTM RMSE: {rmse_lstm:.4f}, MAE: {mae_lstm:.4f}")
