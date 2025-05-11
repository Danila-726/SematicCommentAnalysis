import joblib
import pymorphy3
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

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

    tfidf_vectorizer = joblib.load(r"sklearn-models/tfidf_vectorizer.joblib")

    data[column_with_text+'prep'] = clean_text(data[column_with_text])
    data[column_with_text+'prep'] = lemmatizer_vec(data[column_with_text+'prep'], morph)
    data[column_with_text+'prep'] = tfidf_vectorizer.transform(data[column_with_text+'prep'])

    return clear_void_rows(data, column_with_text+'prep')