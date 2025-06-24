import os
import pandas as pd
import kss
from konlpy.tag import Okt
from gensim import corpora
from gensim.models import LdaMulticore
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from tqdm import tqdm


# ========== 3. 전처리 함수 ==========
def tokenize_article(text, stopwords):
    try:
        okt = Okt()
        sentences = kss.split_sentences(text)
        tokens = []
        for sentence in sentences:
            nouns = okt.nouns(sentence)
            clean_nouns = [w for w in nouns if w not in stopwords and len(w) > 1]
            tokens.extend(clean_nouns)
        return tokens
    except Exception as e:
        print(f"[ERROR] 전처리 실패: {e}")
        return []


# ========== 메인 실행 ==========
def topic_model():
    # ========== 1. 데이터 로드 ==========
    kinds = pd.read_csv("data/interim/news/kinds_news.csv")
    print(f"[INFO] 기사 수: {len(kinds)}")

    # ========== 2. 불용어 로드 ==========
    with open("data/raw/news/stopwords-ko.txt", "r", encoding="utf-8") as f:
        stopwords = [line.strip() for line in f.readlines()]
    print(f"[INFO] 불용어 {len(stopwords)}개 로드 완료")

    # ========== 4. 병렬 전처리 ==========
    print("[INFO] 병렬 전처리 시작...")

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        tokenized_docs = list(tqdm(
            executor.map(partial(tokenize_article, stopwords=stopwords), kinds['content']),
            total=len(kinds),
            desc="전처리 진행중"
        ))

    print("[INFO] 전처리 완료")

    # ========== 5. 사전 및 코퍼스 생성 ==========
    dictionary = corpora.Dictionary(tokenized_docs)
    print(f"[INFO] 사전 생성 완료. 전체 단어 수: {len(dictionary)}")

    corpus = [dictionary.doc2bow(doc) for doc in tokenized_docs]
    print(f"[INFO] 코퍼스 생성 완료. 문서 수: {len(corpus)}")

    # ========== 6. LDA 모델 학습 ==========
    print("[INFO] LDA 모델 학습 시작...")

    lda_model = LdaMulticore(
        corpus=corpus,
        id2word=dictionary,
        num_topics=8,
        random_state=42,
        passes=10,
        workers=os.cpu_count()
    )

    print("[INFO] LDA 모델 학습 완료")

    # ========== 7. 토픽 출력 ==========
    for idx in range(8):
        print(f"\n=== 토픽 #{idx + 1} ===")
        print(lda_model.print_topic(idx, topn=30))