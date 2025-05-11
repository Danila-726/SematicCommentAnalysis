import streamlit as st
from streamlit.components.v1 import html
from service_functions import validate_url, is_url_rutube
import numpy as np
import matplotlib.pyplot as plt
from comment_getter import fetch_comments
from preprocess_text import prepare_data_for_model
from analyze_comment import get_data_with_predicted_label

# Настройка страницы
st.set_page_config(page_title="Анализ данных", layout="wide")

# Инициализация состояния сессии
if 'valid_url' not in st.session_state:
    st.session_state.valid_url = False

st.title("📊 Аналитический инструмент для обработки данных")

# Функция для автоматической прокрутки
def scroll_down():
    html("<script>window.scrollTo(0, document.body.scrollHeight);</script>")

# Основной интерфейс
with st.container():
    st.subheader("Шаг 1: Введите ссылку на данные")
    url = st.text_input("Вставьте ссылку здесь:", placeholder="https://video/video-id")

    if url:
        if validate_url(url):
            st.session_state.valid_url = True
            st.success("✓ Ссылка валидна!")
            scroll_down()
        else:
            st.error("⚠️ Неверный формат ссылки!")
            st.session_state.valid_url = False

# Отображение графиков при валидной ссылке
if st.session_state.valid_url:
    with st.container():
        st.subheader("Шаг 2: Визуализация данных")

        if is_url_rutube(url):
            data = fetch_comments(url)
        else:
            # исправить для вк
            data = fetch_comments(url)

        data, data_for_model = prepare_data_for_model(data, "text")
        data = get_data_with_predicted_label(data_for_model=data_for_model,
                                             data=data,
                                             path_to_model='sklearn-models/log_model.joblib',
                                             column_with_text='text_prep')

        fig, ax = plt.subplots(1, 3, figsize=(10, 2))

        ax[0].pie(data['predicted_label'].value_counts(),
               labels=['negative', 'positive'],
               colors=['#FC5A50', '#9ACD32'],
               autopct='%1.1f%%',
               startangle=90,
               wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'})

        plt.tight_layout(pad=0.5)

        st.pyplot(fig, clear_figure=True)

# Стилизация страницы
st.markdown("""
<style>
    [data-testid="stTextInput"] {
        margin: 10px 0;
    }
    .stPlot {
        box-shadow: 0 0 15px #eee;
        border-radius: 10px;
        padding: 20px;
    }
    .stAlert {
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)