#!/usr/bin/env python
# coding: utf-8

# In[1]:


import re
import nltk
import yake 
from summa import keywords as sk
from keybert import KeyBERT
from googlesearch import search
from bs4 import BeautifulSoup
from urllib.request import urlopen
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize 
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
  
kw_model = KeyBERT(model='all-mpnet-base-v2')

stop_words = set(stopwords.words('english'))
nltk.download('wordnet')
nltk.download('omw-1.4')
lemmatizer = WordNetLemmatizer()
ps = PorterStemmer()

tag_re = re.compile(r'<[^>]+>')


# In[2]:


document = []
query = "Stock" 
for search_results in search(query, tld="com", num=10, stop=10, pause=2):
    try:
        html = urlopen(search_results).read()
        soup = BeautifulSoup(html, features="html.parser")
        document.append(soup)
    except:
        pass


# In[3]:


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

def keyword_extractor(method, corpus, top_n):
    
    if method == 'keybert':
        keybert_keywords = kw_model.extract_keywords(corpus, 
                                     keyphrase_ngram_range=(1,1), 
                                     stop_words='english', 
                                     highlight=False,
                                     top_n=top_n)
        return list(dict(keybert_keywords).keys())
    
    elif method == 'text_rank':
        summa_keywords = list(sk.keywords(corpus, scores=True))
        summa_keys = [word[0] for word in summa_keywords[0:top_n]]
        return summa_keys
    
    elif method == 'yake':
        kw_yake = yake.KeywordExtractor(top=top_n, stopwords=stop_words)
        yake_keywords = kw_yake.extract_keywords(corpus)
        yake_keys = [word[0] for word in yake_keywords]
        return yake_keys
    else:
        print('Error: Key word extraction method not found!')


# In[4]:


clean = []
for doc in range(len(document)):
    clean.append(cleaner(document[doc]))


# In[5]:


keyword_extractor('yake', clean[0], 10)


# In[9]:


keyword_extractor('text_rank', clean[0], 10)


# In[7]:


keyword_extractor('keybert', clean[0], 10)

