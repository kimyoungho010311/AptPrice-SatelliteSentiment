import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Concatenate, GlobalAveragePooling2D
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import os # 파일 경로 조합을 위해 추가
import numpy as np
import pandas as pd

# --- 1. 경로 설정 및 데이터 로드 ---

# ❗️ 1-1. 사용자 설정 경로
TABULAR_DATA_PATH = 'data/interim/sendimental_score_with_sale.csv'
IMAGE_DIRECTORY = 'data/interim/satellites/rot_270' # ❗️ 실제 위성사진이 저장된 폴더 경로를 입력하세요.
IMAGE_EXTENSION = '.jpg' # ❗️ 이미지 파일 확장자 (.png, .jpeg 등)

# 1-2. CSV 파일 로드
df = pd.read_csv(TABULAR_DATA_PATH)

# 1-3. 이미지 전체 경로 생성 (수정된 부분)
# CSV의 행 순서(index)를 기준으로 'apt_image_0.jpg', 'apt_image_1.jpg'... 와 같은 파일명을 생성합니다.
# 이를 통해 CSV의 0번 행은 apt_image_0.jpg 파일과 짝지어집니다.
df['image_filename'] = [f'apt_image_{i}{IMAGE_EXTENSION}' for i in df.index]
df['image_path'] = df['image_filename'].apply(lambda filename: os.path.join(IMAGE_DIRECTORY, filename))

# --- 2. 데이터 전처리 및 분리 ---

# 2-1. 특징(X)과 타겟(y) 분리
# 이제 'image_filename' 컬럼도 원본 특징에서 제외합니다.
X_tabular = df.drop(columns=['면적당 단가(만원)', 'image_path', 'image_filename'])
y_target = df['면적당 단가(만원)']

# 2-2. 숫자형 특징 스케일링
numeric_features = X_tabular.select_dtypes(include=np.number).columns.tolist()
scaler = StandardScaler()
X_tabular[numeric_features] = scaler.fit_transform(X_tabular[numeric_features])


# 2-3. 훈련/테스트 데이터 분리
X_train_tabular, X_test_tabular, \
img_paths_train, img_paths_test, \
y_train, y_test = train_test_split(
    X_tabular,
    df['image_path'],
    y_target,
    test_size=0.2,
    random_state=42
)


# --- 3. 데이터 제너레이터 (수정 없음) ---
def data_generator(tabular_data, image_paths, labels, batch_size, image_shape=(224, 224, 3)):
    num_samples = len(tabular_data)
    while True:
        indices = np.random.permutation(num_samples)
        for offset in range(0, num_samples, batch_size):
            batch_indices = indices[offset:offset+batch_size]
            
            batch_tabular = tabular_data.iloc[batch_indices].values
            batch_paths = image_paths.iloc[batch_indices]
            batch_labels = labels.iloc[batch_indices].values
            
            batch_images = []
            for path in batch_paths:
                try:
                    img = load_img(path, target_size=image_shape[:2])
                    img_array = img_to_array(img) / 255.0
                    batch_images.append(img_array)
                except FileNotFoundError:
                    print(f"Warning: File not found at {path}. Skipping.")
                    continue
            
            if not batch_images: continue
            yield ([np.array(batch_tabular), np.array(batch_images)], np.array(batch_labels))

# --- 4. 모델 생성 및 컴파일 ---
def create_multimodal_model(num_tabular_features, image_shape=(224, 224, 3)):
    # 1) 테이블형 데이터 입력 레이어 정의
    tabular_input = Input(shape=(num_tabular_features,), name='tabular_input')
    
    # 2) 이미지 입력 레이어 정의
    image_input = Input(shape=image_shape, name='image_input')
    
    # 3) 테이블형 데이터 처리: Dense 레이어 2개
    x1 = Dense(64, activation='relu')(tabular_input)  # 첫 번째 은닉층
    tabular_features = Dense(32, activation='relu')(x1)  # 두 번째 은닉층으로 최종 테이블 피처 생성
    
    # 4) 이미지 처리: 사전 학습된 ResNet50 사용
    base_cnn = ResNet50(weights='imagenet', include_top=False, input_tensor=image_input)
    base_cnn.trainable = False  # ResNet50 가중치는 고정하여 특징 추출만 사용
    
    # 5) CNN 출력 처리: GlobalAveragePooling2D로 피처 차원 축소
    x2 = GlobalAveragePooling2D()(base_cnn.output)
    x2 = Dense(128, activation='relu')(x2)  # 중간 Dense 레이어
    image_features = Dense(64, activation='relu')(x2)  # 최종 이미지 피처 벡터
    
    # 6) 테이블형 피처와 이미지 피처 결합
    combined_features = Concatenate()([tabular_features, image_features])
    
    # 7) 결합된 피처로 최종 예측 레이어 전 처리
    final_dense = Dense(64, activation='relu')(combined_features)
    
    # 8) 최종 출력 레이어: 아파트 가격 예측 (회귀)
    prediction = Dense(1, activation='linear', name='price_output')(final_dense)
    
    # 9) 모델 정의
    model = Model(inputs=[tabular_input, image_input], outputs=prediction)
    
    return model

# 10) 테이블형 피처 개수 확인
num_features = X_train_tabular.shape[1]

# 11) 모델 생성
model = create_multimodal_model(num_tabular_features=num_features)

# 12) 모델 컴파일: optimizer=Adam, loss=MSE, 평가 지표=MAE
model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])

# 13) 모델 구조 확인
model.summary()

# --- 5. 모델 학습 ---
BATCH_SIZE = 32
EPOCHS = 20

train_gen = data_generator(X_train_tabular, img_paths_train, y_train, BATCH_SIZE)
test_gen = data_generator(X_test_tabular, img_paths_test, y_test, BATCH_SIZE)

history = model.fit(
    train_gen,
    steps_per_epoch=len(X_train_tabular) // BATCH_SIZE,
    epochs=EPOCHS,
    validation_data=test_gen,
    validation_steps=len(X_test_tabular) // BATCH_SIZE
)