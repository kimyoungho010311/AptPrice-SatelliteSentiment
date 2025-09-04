
import pandas as pd
import json
from konlpy.tag import Mecab
import numpy as np
from tqdm import tqdm

def label_sentiment(news_path, sentiment_dict_path, output_path):
    # Load sentiment dictionary
    with open(sentiment_dict_path, 'r', encoding='utf-8') as f:
        senti_dict_list = json.load(f)
    
    senti_dict = {item['word']: int(item['polarity']) for item in senti_dict_list}

    # Initialize Mecab
    mecab = Mecab()

    # Read news data
    df = pd.read_csv(news_path)

    # Randomly sample 1000 rows
    # if len(df) > 1000:
    #     df = df.sample(n=1000, random_state=42)
    
    # Define a function to calculate sentiment score
    def get_sentiment_score(text):
        if not isinstance(text, str):
            return 0
        
        words = mecab.morphs(text)
        score = 0
        for word in words:
            score += senti_dict.get(word, 0)
        return score

    # Apply the function to the content column
    tqdm.pandas(desc="Calculating sentiment")
    df['sentiment'] = df['content'].progress_apply(get_sentiment_score)

    # Save the result
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Sentiment analysis complete. Labeled data saved to {output_path}")

if __name__ == '__main__':
    news_path = '/Users/kim-youngho/git/AptPrice-SatelliteSentiment/data/interim/news/kinds_news.csv'
    sentiment_dict_path = '/Users/kim-youngho/git/AptPrice-SatelliteSentiment/data/raw/news/SentiWord_info.json'
    output_path = '/Users/kim-youngho/git/AptPrice-SatelliteSentiment/data/interim/news/kinds_news_labeled.csv'
    label_sentiment(news_path, sentiment_dict_path, output_path)
