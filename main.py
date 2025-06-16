# 뉴스 크롤링
from script.crawling.chosun_ilbo import crawling_chosun
from script.crawling.dong_a_ilbo import crawling_dong_a

# 크롤링 뉴스 전처리
from script.prepro_news.prepro_chosun import prepro_chosun
from script.prepro_news.prepro_dong_a import prepro_dong_a

def main():
    # 조선일보 뉴스기사 수집.
    #crawling_chosun(400)
    #prepro_chosun()
    # 400까지?
    crawling_dong_a(400)
    prepro_dong_a()

# soruce ~~
if __name__ == '__main__':
    main()