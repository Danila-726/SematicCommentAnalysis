import joblib
import pymorphy3
import re
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string

def clean_stop_words(text):
    stop_words = set(stopwords.words('russian'))
    punctuation = set(string.punctuation)
    words = word_tokenize(text.lower())
    filtered_words = [word for word in words if word not in stop_words and word not in punctuation]
    return " ".join(filtered_words)

def lemmatizer(text, morph):
    pymorphy_results = list(map(lambda x: morph.parse(x), text.split(' ')))
    return ' '.join([res[0].normal_form for res in pymorphy_results])

def clean(text):
    text = text.replace("ё", "е").replace("RT ", "")
    text = re.sub('[^а-яА-Я]+', ' ', text)
    text = re.sub(' +',' ', text)
    return text.strip()

def clear_void_rows(data, column):
    data_with_void = data[data[column] == ""].index
    data = data.iloc[[id for id in data.index if id not in data_with_void]]
    return data

def prepare_data_for_model(data, column_with_text):
    clean_text = np.vectorize(clean)
    lemmatizer_vec = np.vectorize(lemmatizer)
    morph = pymorphy3.MorphAnalyzer()
    nltk.download('stopwords')
    nltk.download('punkt')
    nltk.download('punkt_tab')

    tfidf_vectorizer = joblib.load(r"sklearn-models/tfidf_vectorizer.joblib")

    data[f"{column_with_text}_prep"] = clean_text(data[column_with_text])
    data[f"{column_with_text}_prep"] = lemmatizer_vec(data[f"{column_with_text}_prep"], morph)
    data = clear_void_rows(data, column_with_text+'_prep')
    data[column_with_text + '_prep_stop_words'] = data[column_with_text + '_prep'].apply(clean_stop_words)
    vectorized_data = tfidf_vectorizer.transform(data[f"{column_with_text}_prep"])

    return data, vectorized_data