# 노트북에 모든 함수를 이 파일에 집어넣는다.
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Concatenate, GlobalAveragePooling2D, LSTM, BatchNormalization, GRU, Attention, GlobalAveragePooling1D
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.layers import Dropout
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rc
import seaborn as sns

def create_feature_extractor_model(num_tabular_features, image_shape=(224, 224, 3)):
    """다중 모달(정형+이미지) 입력을 받아 특징 벡터를 추출하는 모델을 생성합니다.

    정형 데이터와 이미지 데이터를 각각 별도의 신경망으로 처리한 후,
    두 특징을 결합하여 최종 특징 벡터를 생성합니다. 이 벡터는
    후속 시계열 모델의 입력으로 사용될 수 있습니다.

    Args:
        num_tabular_features (int): 정형 데이터의 특징(컬럼) 개수.
        image_shape (tuple): 입력 이미지의 형태 (높이, 너비, 채널).

    Returns:
        tf.keras.Model: 정형 및 이미지 데이터를 입력받아
                        256차원의 특징 벡터를 출력하는 Keras 모델.
    """
    # --- 입력층 정의 ---
    tabular_input = Input(shape=(num_tabular_features,), name='tabular_input')
    image_input = Input(shape=image_shape, name='image_input')
    
    # --- 특징별 처리 스트림 ---
    base_cnn = ResNet50(weights='imagenet', include_top=False, input_tensor=image_input)
    base_cnn.trainable = False
    x_image = GlobalAveragePooling2D()(base_cnn.output)
    x_image = Dense(128, activation='relu')(x_image)
    image_features = Dense(64, activation='relu')(x_image)

    tabular_features = Dense(64, activation='relu')(tabular_input)
    
    # --- 특징 결합 ---
    combined = Concatenate()([image_features, tabular_features])
    normalized_features = BatchNormalization()(combined)
    x = Dense(256, activation='relu')(normalized_features)
    
    # --- 모델 생성 ---
    model = Model(inputs=[tabular_input, image_input], outputs=x, name='apartment_predictor')
    
    return model


def prediction_generator(tabular_data, image_paths, batch_size, image_shape=(224, 224, 3)):
    """특징 추출 모델에 데이터를 공급하기 위한 제너레이터(generator)입니다.

    정형 데이터와 이미지 파일 경로를 받아 배치(batch) 단위로 묶어,
    모델의 입력 형태에 맞는 딕셔너리 형태로 데이터를 생성합니다.
    이미지 파일을 찾을 수 없는 경우, 0으로 채워진 배열을 생성하여 처리합니다.

    Args:
        tabular_data (pd.DataFrame): 스케일링된 정형 특징 데이터.
        image_paths (pd.Series): 이미지 파일의 전체 경로.
        batch_size (int): 한 번에 처리할 데이터의 양.
        image_shape (tuple): 불러올 이미지의 크기.

    Yields:
        dict: 모델의 입력 이름('tabular_input', 'image_input')을 키로 하고,
              배치 데이터를 값으로 하는 딕셔너리.
    """
    num_samples = len(tabular_data)
    for offset in range(0, num_samples, batch_size):
        batch_tabular = tabular_data.iloc[offset:offset+batch_size].values.astype(np.float32)
        batch_paths = image_paths.iloc[offset:offset+batch_size]
        
        batch_images = []
        for path in batch_paths:
            try:
                img = load_img(path, target_size=image_shape[:2])
                img_array = img_to_array(img) / 255.0
                batch_images.append(img_array)
            except FileNotFoundError:
                batch_images.append(np.zeros(image_shape, dtype=np.float32))
        
        yield {
            'tabular_input': np.array(batch_tabular, dtype=np.float32),
            'image_input': np.array(batch_images, dtype=np.float32)
        }


def create_sequences(X_data, y_data, lookback):
    """일반적인 시계열 데이터를 생성하는 함수입니다.

    주어진 전체 데이터를 'lookback' 길이에 맞는 시퀀스(sequence) 데이터로 변환합니다.
    예를 들어, lookback=10이면 과거 10일치 데이터를 보고 다음날을 예측하는
    형태의 데이터셋을 만듭니다.

    Args:
        X_data (np.ndarray): 입력 특징 데이터 배열.
        y_data (np.ndarray): 타겟 데이터 배열.
        lookback (int): 과거를 돌아볼 기간 (하나의 시퀀스를 구성할 길이).

    Returns:
        tuple: 다음을 포함하는 튜플:
            - np.ndarray: 생성된 입력 시퀀스 (X_sequences).
            - np.ndarray: 생성된 타겟 시퀀스 (y_sequences).
    """
    X_sequences, y_sequences = [], []
    for i in range(len(X_data) - lookback):
        X_sequences.append(X_data[i:(i + lookback)])
        y_sequences.append(y_data[i + lookback])
    return np.array(X_sequences), np.array(y_sequences)


def create_lstm_model(input_shape):
    """시계열 예측을 위한 간단한 LSTM 모델을 생성합니다.

    두 개의 LSTM 레이어와 하나의 Dense 출력 레이어로 구성된 모델을 정의합니다.
    과적합을 방지하기 위해 Dropout이 포함되어 있습니다.

    Args:
        input_shape (tuple): 모델의 입력 형태 (타임스텝, 특징 수).

    Returns:
        tf.keras.Model: 컴파일되지 않은 LSTM Keras 모델.
    """
    input_layer = Input(shape=input_shape)
    # ❗️ [팁] LSTM의 활성화 함수는 기본값인 'tanh'를 사용하는 것이 안정적입니다.
    x = LSTM(128, return_sequences=True)(input_layer)
    x = Dropout(0.2)(x)
    # 마지막 LSTM 레이어에서는 return_sequences=False가 일반적입니다.
    x = LSTM(64, return_sequences=False)(x)  
    prediction = Dense(1, activation='linear')(x)

    model = Model(inputs=input_layer, outputs=prediction, name='lstm_forecaster')
    return model

def create_future_sequences(all_features, original_df, lookback=10, horizon_days=30):
    """특정 미래 시점의 가격을 예측하기 위한 시계열 데이터셋을 생성합니다.

    과거 'lookback' 기간의 데이터를 사용하여 'horizon_days' 후의 가격을
    예측하는 입출력(X, y) 데이터 쌍을 만듭니다. 예를 들어, 1월 1일~10일
    데이터를 보고 30일 후인 2월 9일의 가격을 예측하는 식입니다.

    Args:
        all_features (np.ndarray): (샘플 수, 특징 수) 모양의 전체 특징 데이터.
        original_df (pd.DataFrame): '계약일자'와 타겟 컬럼이 포함된 원본 데이터프레임.
        lookback (int): 과거를 돌아볼 기간 (입력 시퀀스 길이).
        horizon_days (int): 예측할 미래 시점 (단위: 일).

    Returns:
        tuple: 다음을 포함하는 튜플:
            - np.ndarray: 생성된 입력 시퀀스 (X_sequences).
            - np.ndarray: 생성된 미래 시점의 타겟 값 (y_sequences).
    """
    X_sequences, y_sequences = [], []
    
    dates = original_df['계약일자']
    # ❗️ [수정] 전역 변수 대신 파라미터로 받은 df를 사용해야 합니다.
    targets = original_df['면적당 단가(만원)'].values # 예시 타겟 컬럼명
    
    for i in range(len(all_features) - lookback):
        end_of_input_sequence_date = dates.iloc[i + lookback - 1]
        target_date = end_of_input_sequence_date + pd.Timedelta(days=horizon_days)
        future_data_indices = np.where(dates >= target_date)[0]
        
        if len(future_data_indices) > 0:
            future_target_index = future_data_indices[0]
            if future_target_index < len(all_features):
                X_sequences.append(all_features[i:(i + lookback)])
                y_sequences.append(targets[future_target_index])
                
    return np.array(X_sequences), np.array(y_sequences)

def analyze_and_visualize_model(model, X_test_seq, y_test_seq, model_name):
    """학습된 모델의 성능을 분석하고 결과를 시각화합니다.

    모델의 예측값과 실제값을 비교하여 실제 단위(만원) 기준의 MAE를 계산하고,
    결과를 Scatter Plot으로 시각화하여 모델의 성능을 직관적으로 보여줍니다.
    로그 변환된 타겟을 사용한 모델을 가정하고 내부적으로 역변환을 수행합니다.

    Args:
        model (tf.keras.Model): 학습이 완료된 Keras 모델.
        X_test_seq (np.ndarray): 테스트용 입력 시퀀스 데이터.
        y_test_seq (np.ndarray): 테스트용 정답 데이터 (로그 변환된 값).
        model_name (str): 그래프 제목 등에 표시될 모델의 이름.
    """
    print(f"\n--- {model_name} 모델 성능 분석 시작 ---")
    
    # 1. 예측 수행 및 역변환
    y_pred_log = model.predict(X_test_seq).flatten()
    y_pred_original = np.expm1(y_pred_log)
    
    y_test_original = np.expm1(y_test_seq.flatten())
    
    # 2. 예측값과 실제값 길이 맞추기
    min_len = min(len(y_test_original), len(y_pred_original))
    y_test_np = y_test_original[:min_len]
    y_pred_original = y_pred_original[:min_len]

    # 3. 실제 단위(만원)로 MAE 계산
    real_world_mae = mean_absolute_error(y_test_np, y_pred_original)

    # 4. 결과 출력
    print(f"--- {model_name}: 실제 값 vs 예측 값 비교 (원본 단위, 상위 5개) ---")
    for i in range(min(5, len(y_test_np))):
        print(f"실제 단가: {y_test_np[i]:.2f} (만원)  |  예측 단가: {y_pred_original[i]:.2f} (만원)")

    print(f"\n--- {model_name}: 최종 실제 오차 (원본 단위) ---")
    print(f"Real World MAE: {real_world_mae:.2f} (만원)")

    # 5. 시각화
    plt.figure(figsize=(10, 10))
    plt.scatter(y_test_np, y_pred_original, alpha=0.5, label='예측 결과')
    
    min_val = min(y_test_np.min(), y_pred_original.min())
    max_val = max(y_test_np.max(), y_pred_original.max())
    
    plt.plot([min_val, max_val], [min_val, max_val], 
             '--r', linewidth=2, label='완벽한 예측선 (y=x)')
    
    plt.xlabel("실제 면적당 단가 (만원)", fontsize=14)
    plt.ylabel("예측 면적당 단가 (만원)", fontsize=14)
    plt.title(f"실제 가격 vs. 모델 예측 가격 ({model_name})", fontsize=16)
    plt.legend()
    plt.grid(True)
    plt.show()