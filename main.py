# 뉴스 크롤링
from script.crawling.chosun_ilbo import crawling_chosun
from script.crawling.dong_a_ilbo import crawling_dong_a
from script.crawling.joonang_ilbo import crawling_joonang

# 크롤링 뉴스 전처리
from script.prepro_news.prepro_chosun import prepro_chosun
from script.prepro_news.prepro_dong_a import prepro_dong_a
from script.prepro_news.prepro_joongang import prepro_joongang

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
 
# soruce ~~
if __name__ == '__main__':
    main()