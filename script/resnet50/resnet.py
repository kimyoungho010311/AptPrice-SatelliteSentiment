from pathlib import Path
import os
import numpy as np
import pandas as pd
from tqdm.notebook import tqdm
from tensorflow.keras.applications import ResNet50
#from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.layers import Input, Dense, Concatenate
from tensorflow.keras import Model
#from tensorflow.keras.optimizers import Adam
#from sklearn.neural_network import MLPRegressor
#from sklearn.model_selection import KFold
#from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
#from sklearn.preprocessing import MinMaxScaler
from PIL import Image, UnidentifiedImageError
import tensorflow as tf

def run_resnet():

    SALE_PATH = '/Users/kim-youngho/git/AptPrice-SatelliteSentiment/data/interim/apt/apt_with_long_lat.csv'
    IMAGES_DIR = '/Users/kim-youngho/git/AptPrice-SatelliteSentiment/data/interim/satellites/rot_90'

    sale = pd.read_csv(SALE_PATH)
    sale.dropna(inplace=True)

    print(sale.info())

    # ===== 이미지 피처 추출 (OpenCV 사용) ===== #
    valid_exts = ('.jpg', '.jpeg', '.png')
    image_paths = [
        os.path.join(IMAGES_DIR, fname)
        for fname in sorted(os.listdir(IMAGES_DIR))
        if os.path.isfile(os.path.join(IMAGES_DIR, fname)) and fname.lower().endswith(valid_exts)
    ]
    len(image_paths)

    def extract_image_features(image_paths, resnet_model):
        features = []
        for path in tqdm(image_paths):
            try:
                # OpenCV로 이미지 로드
                import cv2
                img = cv2.imread(path)
                if img is None:
                    print(f"⚠️ 이미지 읽기 실패: {path}")
                    continue

                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # RGB 변환
                img = cv2.resize(img, (224, 224))  # ResNet50 입력 크기

                # 배열 변환 및 전처리
                x = np.expand_dims(img, axis=0)
                x = tf.keras.applications.resnet50.preprocess_input(x)

                # 피처 추출
                feat = resnet_model.predict(x, verbose=0)
                features.append(feat.flatten())
            except Exception as e:
                print(f"❌ 예기치 않은 에러: {path} - {e}")
        return np.array(features)

    # ResNet50 모델

    base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg', input_shape=(224,224,3))
    fc = Dense(2048, activation=None, trainable=False)(base_model.output)
    resnet_model = Model(inputs=base_model.input, outputs=fc)

    # 피처 추출
    image_features = extract_image_features(image_paths, resnet_model)
    df_image_features = pd.DataFrame(image_features, columns=[f'feature_{i}' for i in range(image_features.shape[1])])
    df_price = sale[['면적당 단가(만원)']].reset_index(drop=True)

    print(f"length of df_image_features is : {len(df_image_features)}")
    print(f"length of sale is : {len(sale)}")

    if len(df_image_features) == len(sale):
        print("Length of two df is same. Let's concat")
        print("Saved directory is '../data/interim/..'")
        df_combined = pd.concat([sale, df_image_features], axis=1)
        df_combined.dropna(inplace=True)
        df_combined.to_csv("../data/interim/resnet90deg.csv", index=False)
    else:
        print("두 데이터의 길이가 다릅니다. 병합이 불가능합니다.")