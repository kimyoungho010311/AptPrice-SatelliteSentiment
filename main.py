# 뉴스 크롤링
from script.crawling.chosun_ilbo import crawling_chosun
from script.crawling.dong_a_ilbo import crawling_dong_a
from script.crawling.joonang_ilbo import crawling_joonang
from script.crawling.korea_economy import crawling_korea

# 크롤링 뉴스 전처리
from script.prepro_news.prepro_chosun import prepro_chosun
from script.prepro_news.prepro_dong_a import prepro_dong_a
from script.prepro_news.prepro_joongang import prepro_joongang
from script.prepro_news.prepro_korea import prepro_korea

# 매매데이터 전처리
from script.prepro_apt.prepro_apt import prepro_apt

# 토픽 모델링
from script.topic_modeling.lda_topic_model import topic_model

# 중복거래 전처리 비교 실험
from script.Compare_duplicate_sale.untitled import (
    load_and_preprocess_data,
    prepare_way1,
    prepare_way2,
    prepare_data,
    train_mlp,
    train_lstm
)
def main():
    # 조선일보
    #crawling_chosun(400)
    #prepro_chosun()

    # 동아일보
    #crawling_dong_a(400)
    #prepro_dong_a()

    # 중앙일보
    #crawling_joonang(1)
    #prepro_joongang()
 
    # 한국경제
    #crawling_korea(1000)
    #prepro_korea()

    # 토픽 모델링
    #topic_model()

    # 중복위치 거래 실험 
    # folder_path = "data/raw/apt_sale"
    # df = load_and_preprocess_data(folder_path)
    # way1 = prepare_way1(df)
    # way2 = prepare_way2(df)

    # print("\n[부동산 예측] Way1 MLP 학습 및 평가 시작")
    # X1, y1 = prepare_data(way1, use_alpha=False)
    # mlp_rmse1, mlp_mae1 = train_mlp(X1, y1)

    # print("[부동산 예측] Way1 LSTM 학습 및 평가 시작")
    # lstm_rmse1, lstm_mae1 = train_lstm(X1, y1)


    # print("\n[부동산 예측] Way2 MLP 학습 및 평가 시작")
    # X2, y2 = prepare_data(way2, use_alpha=True)
    # mlp_rmse2, mlp_mae2 = train_mlp(X2, y2)

    # print("[부동산 예측] Way2 LSTM 학습 및 평가 시작")
    # lstm_rmse2, lstm_mae2 = train_lstm(X2, y2)

    # print(f"\n[부동산 예측 최종 결과] Way1 - MLP RMSE: {mlp_rmse1:.4f}, MAE:{mlp_mae1:.4f}")
    # print(f"[부동산 예측 최종 결과] Way1 - LSTM RMSE: {lstm_rmse1:.4f}, MAE: {lstm_mae1:.4f}")

    # print(f"\n[부동산 예측 최종 결과] Way2 - MLP RMSE: {mlp_rmse2:.4f}, MAE: {mlp_mae2:.4f}")
    # print(f"[부동산 예측 최종 결과] Way2 - LSTM RMSE: {lstm_rmse2:.4f}, MAE: {lstm_mae2:.4f}")

    prepro_apt()
# soruce ~~
if __name__ == '__main__':
    main()