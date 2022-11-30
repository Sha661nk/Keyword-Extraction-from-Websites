import json
from Package_Installer.package_installer import installed
from stopwords import stopwords_array

installed("google")

import boto3
import re
import nltk
import yake 
import time
import pandas as pd
from googlesearch import search
from bs4 import BeautifulSoup
from urllib.request import urlopen
from nltk.tokenize import word_tokenize 
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
             
stop_words = stopwords_array()

nltk.data.path.append("/tmp")
nltk.download('wordnet', download_dir="/tmp")
nltk.download('omw-1.4', download_dir="/tmp")

lemmatizer = WordNetLemmatizer()
ps = PorterStemmer()

tag_re = re.compile(r'<[^>]+>')

def scrapper(query_string, num_of_pages, stop_at):
    document = []
    for search_results in search(query_string, tld="com", num=num_of_pages, stop=stop_at, pause=2):
        try:
            html = urlopen(search_results).read()
            soup = BeautifulSoup(html, features="html.parser")
            document.append(soup.body)
        except:
            pass
    return (document)

def cleaner(x): 
    brackets_removed = tag_re.sub('', str(x))
    new_line_removed = str(brackets_removed).replace(r'\n', ' ')
    email_removed = re.sub(r'[A-Za-z0-9]*@[A-Za-z]*\.?[A-Za-z0-9]*', ' ', new_line_removed)
    symbols_removed = re.sub('[^A-Za-z0-9]+', ' ', email_removed)
    clean_data = re.sub(r"(^|\W)\d+", ' ', symbols_removed)  
    clean_data = lemmatizer.lemmatize(clean_data)
    clean_data = ps.stem(clean_data)
    clean_data = clean_data.replace('\n','')
    return clean_data

def keyword_extractor(method, corpus, top_n, max_ngram_size):
    try:
        if method == 'yake':
            kw_yake = yake.KeywordExtractor(top=top_n, stopwords=stop_words, n=max_ngram_size)
            yake_keywords = kw_yake.extract_keywords(corpus)
            yake_keys = [word[0] for word in yake_keywords]
            return yake_keys
        else:
            print('Extractor not found!')

    except:
        # Slow Keyword Extractor
        installed('keybert')
        from keybert import KeyBERT
        kw_model = KeyBERT('paraphrase-multilingual-MiniLM-L12-v2')
        keybert_keywords = kw_model.extract_keywords(corpus, 
                                         keyphrase_ngram_range=(1, max_ngram_size), 
                                         stop_words='english', 
                                         highlight=False,
                                         top_n=10)
        return list(dict(keybert_keywords).keys())

def driver(query_string, num_of_pages, stop_at, top_n_words, grams, method):
    data = []
    for query in query_string:
        document = scrapper(query, num_of_pages, stop_at)
        ngrams  = []
        for doc in range(len(document)):
            ngrams.append(keyword_extractor(method, cleaner(document[doc]), top_n_words, grams))

        n_keywords = [ngram for ngram_list in ngrams for ngram in ngram_list]
        n_keywords = list(filter(lambda x: set(x.split(' ')).isdisjoint(stop_words), n_keywords))

        keys = [[common_keywords, n_keywords.count(common_keywords)] for common_keywords in set(n_keywords)] 
        keyword_freq = pd.DataFrame(keys, columns=['Keyword', 'Freq']).sort_values(by='Freq', ascending=False).reset_index(drop=True)
        keyword_freq = keyword_freq[keyword_freq["Freq"] > 3]
        keyword_freq['Query'] = query
        data.append(keyword_freq)

    final_keys = pd.concat(data)
    return final_keys.to_dict('records')

def lambda_handler(event, context):
    query_string = event['query_string']
    num_of_pages = event['num_of_pages']
    stop_at = event['stop_at']
    top_n_words = event['top_n_words']
    grams = event['grams']
    method = event['method']
    
    keyword_file = driver(query_string, num_of_pages, stop_at, top_n_words, grams, method)
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('keyword_data')
    
    for item in keyword_file:
        keyword = item['Keyword']
        freq = item['Freq']
        query = item['Query']

        table.put_item(Item={'keyword': keyword,
                             'freq': freq,
                             'query': query})

    return print('Records has been updated!')