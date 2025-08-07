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

# 위도 경도 추출
from script.get_longitudes_latitudes.get_longitudes_latitudes import get_longitudes_latitudes

# 위성지도 수집
from script.satellite_image.combine_satellite import combine_satellite

# 위성사진 전처리
from script.prepro_satellite.prepro_satellite import prepro_satellite


# 토픽 모델링
from script.topic_modeling.lda_topic_model import topic_model

def main():
    # 조선일보
    # crawling_chosun(400)
    # prepro_chosun()

    # # 동아일보
    # crawling_dong_a(400)
    # prepro_dong_a()

    # # 중앙일보
    # crawling_joonang(400)
    # prepro_joongang()
 
    # # 한국경제
    # crawling_korea(400)
    # prepro_korea()

    # 토픽 모델링
    #topic_model()


    # 아파트 중복거래, 컬럼 삭제등 전처리
    #prepro_apt()

    # 아파트 위경도 수집
    #get_longitudes_latitudes()

    # 위성사진 수집
    combine_satellite()

    # 위성사진 전처리
    #prepro_satellite()
# soruce ~~
if __name__ == '__main__':
    main()