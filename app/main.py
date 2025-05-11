import streamlit as st
from streamlit.components.v1 import html
from service_functions import validate_url
import numpy as np
import matplotlib.pyplot as plt

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



        # Генерация случайных данных для примера
        np.random.seed(42)
        data = np.random.randn(100, 3)

        # Создание графиков
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

        # Линейный график
        ax1.plot(data)
        ax1.set_title("Динамика показателей")
        ax1.legend(["Показатель 1", "Показатель 2", "Показатель 3"])

        # Гистограмма
        ax2.hist(data, bins=15, alpha=0.5)
        ax2.set_title("Распределение данных")
        ax2.legend(["Показатель 1", "Показатель 2", "Показатель 3"])

        plt.tight_layout()
        st.pyplot(fig)

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