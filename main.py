from script.crawling.chosun_ilbo import crawling_chosun


def main():
    # 조선일보 뉴스기사 수집.
    crawling_chosun(400)

# 가상환경으로 시작하자!!!
# soruce ~~
if __name__ == '__main__':
    main()