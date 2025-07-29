import streamlit as st
import base64
import random
from service_functions import validate_url, is_url_rutube
import matplotlib.pyplot as plt
from comment_getter import get_rutube_comments, get_vk_comments
from preprocess_text import prepare_data_for_model
from analyze_comment import get_data_with_predicted_label
from wordcloud import WordCloud
import pandas as pd

mems = ['content/atlant.png',
        'content/chill.png',
        'content/dog krevetka.png',
        'content/dopros.png',
        'content/dude.png',
        'content/fun dog.png',
        'content/kirieshki.png',
        'content/lobanov.png',
        'content/okak.png',
        'content/smiling cat.png']
your_version = 12345
your_client_id = 12345
your_client_secret = ""
your_app_id = 123456

st.set_page_config(page_title="Семантический анализ комментариев", layout="wide")

def get_image_base64(path):
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return f"data:image/png;base64,{encoded_string}"

if 'valid_url' not in st.session_state:
    st.session_state.valid_url = False

st.markdown("""
<style>
    .stAppHeader,
    .stDecoration,
    .stAppToolbar,
    .stToolbarActions,
    .stAppDeployButton {
        display: none !important;
    }
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        backdrop-filter: blur(3px);
        -webkit-backdrop-filter: blur(3px);
        background-color: rgba(255, 255, 255, 0.7);
        z-index: 9998;
        opacity: 0;
        animation: fadeIn 0.3s ease-out forwards;
    }
    .loading-container {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -45%);
        z-index: 9999;
        text-align: center;
        opacity: 0;
        animation: fadeInUp 0.4s ease-out 0.1s forwards;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translate(-50%, -45%);
        }
        to {
            opacity: 1;
            transform: translate(-50%, -50%);
        }
    }
    .dot-loader {
        --uib-size: 90px;
        --uib-speed: 1.3s;
        --uib-color: #000000;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        height: var(--uib-size);
        width: var(--uib-size);
        margin: 0 auto 25px;
    }
    .dot-loader__dot {
        position: absolute;
        top: 0;
        left: 0;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        height: 100%;
        width: 100%;
    }
    .dot-loader__dot::before {
        content: '';
        height: 25%;
        width: 25%;
        border-radius: 80%;
        background-color: var(--uib-color);
        transform: scale(0);
        transition: background-color 0.3s ease;
        animation: pulse var(--uib-speed) ease-in-out infinite;
    }
    
    .dot-loader__dot:nth-child(2) { transform: rotate(45deg); }
    .dot-loader__dot:nth-child(2)::before { animation-delay: calc(var(--uib-speed) * -0.875); }

    .dot-loader__dot:nth-child(3) { transform: rotate(90deg); }
    .dot-loader__dot:nth-child(3)::before { animation-delay: calc(var(--uib-speed) * -0.75); }

    .dot-loader__dot:nth-child(4) { transform: rotate(135deg); }
    .dot-loader__dot:nth-child(4)::before { animation-delay: calc(var(--uib-speed) * -0.625); }

    .dot-loader__dot:nth-child(5) { transform: rotate(180deg); }
    .dot-loader__dot:nth-child(5)::before { animation-delay: calc(var(--uib-speed) * -0.5); }

    .dot-loader__dot:nth-child(6) { transform: rotate(225deg); }
    .dot-loader__dot:nth-child(6)::before { animation-delay: calc(var(--uib-speed) * -0.375); }

    .dot-loader__dot:nth-child(7) { transform: rotate(270deg); }
    .dot-loader__dot:nth-child(7)::before { animation-delay: calc(var(--uib-speed) * -0.25); }

    .dot-loader__dot:nth-child(8) { transform: rotate(315deg); }
    .dot-loader__dot:nth-child(8)::before { animation-delay: calc(var(--uib-speed) * -0.125); }

    @keyframes pulse {
        0%, 100% {
            transform: scale(0.4);
            opacity: 0.7;
        }
        50% {
            transform: scale(0.8);
            opacity: 1;
        }
    }
    .loading-spinner { display: none !important; }
    h1 {
        text-align: center !important;
        width: 100% !important;
        padding: 5px 0 !important;
        color: #000000 !important; 
        text-shadow: 0px 0px 1px rgba(0,0,0,1);
    }
    div[data-testid="stVerticalBlock"] > div:first-child {
        justify-content: center !important;
    }
    @media (max-width: 770px) {
        .logo-row img {
            width: 80px !important;
        }
    }
    div[role="progressbar"] > div > div {
        background-color: #ffffff !important;
    }
    div[role="progressbar"] > div {
        border: 2px solid #000000 !important;
        border-radius: 8px !important;
        padding: 1px !important;
    }
    .stProgress > div > div > div > div {
        background-color: #000000 !important; 
    }
    
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="display: flex; flex-direction: column; align-items: center; margin: 0 auto 25px;">
    <div style="display: flex; gap: 20px; margin-bottom: 30px;">
        <img src="{get_image_base64('content/rutube_logo.png')}" width="100">
        <img src="{get_image_base64('content/vkvideo_logo.png')}" width="100">
    </div>
    <h1>Семантический анализ комментариев</h1>
</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("""
        <style>
            div[data-testid="stTextInput"] {
                max-width: 500px;
                margin: 0 auto;
                position: relative;
                padding: 0px 0px;
                border: none !important;
                box-shadow: none !important;
                background: transparent !important;
            }
            div[data-testid="stTextInput"] > div {
                border: none !important;
                box-shadow: none !important;
                background: transparent !important;
                border-radius: 15px;
                color: transparent !important
            }
            div[data-testid="stTextInput"] label {
                position: absolute;
                left: 3px;
                top: -25%;
                transform: translateY(-50%);
                padding: 0.5px;
                font-size: 10.0em;
                pointer-events: none;
                transition: all 0.3s ease;
            }
            div[data-testid="stTextInput"] input {
                width: 100% !important;
                border: 2px solid #e0e0e0;
                border-radius: 15px;
                transition: all 0.3s ease;
            }
            div[data-testid="stTextInput"] input:focus {
                border-color: #1e88e5;
                box-shadow: 0 0 0 2px rgba(30,136,229,0.2);
            }
        </style>
        """, unsafe_allow_html=True)

    url = st.text_input("Вставьте ссылку здесь:", placeholder="Начните вводить...")

    if url:
        if validate_url(url):
            st.session_state.valid_url = True
            border_color = "#4CAF50"
            background_color = "#E8F5E9"
            text_color = "#1B5E20"
        else:
            st.session_state.valid_url = False
            border_color = "#FF0000"
            background_color = "#FFEBEE"
            text_color = "#B71C1C"

        box_shadow_color = border_color + "33"

        st.markdown(f"""
            <style>
                div[data-testid="stTextInput"] input {{
                    border: 2px solid {border_color} !important;
                    background-color: {background_color} !important;
                    color: {text_color} !important;
                    font-weight: 500;
                }}
                div[data-testid="stTextInput"] input::placeholder {{
                    color: {text_color}88 !important;
                }}
                div[data-testid="stTextInput"] input:focus {{
                    border-color: {border_color} !important;
                    box-shadow: 0 0 0 2px {box_shadow_color} !important;
                    background-color: {background_color} !important;
                }}
            </style>
            """, unsafe_allow_html=True)

if st.session_state.valid_url:
    with (st.container()):
        loading_placeholder = st.empty()
        loading_placeholder.markdown("""
            <div class="loading-overlay"></div>
            <div class="loading-container">
                <div class="dot-loader">
                    <div class="dot-loader__dot"></div>
                    <div class="dot-loader__dot"></div>
                    <div class="dot-loader__dot"></div>
                    <div class="dot-loader__dot"></div>
                    <div class="dot-loader__dot"></div>
                    <div class="dot-loader__dot"></div>
                    <div class="dot-loader__dot"></div>
                    <div class="dot-loader__dot"></div>
                </div>
                <div style="font-size: 24px; font-weight: bold; color: #000000;">Загрузка комментариев...</div>
            </div>
        """, unsafe_allow_html=True)
        try:
            if is_url_rutube(url):
                data = get_rutube_comments(url)
            else:
                data = get_vk_comments(url, your_version, your_client_id, your_client_secret, your_app_id, 0.5)
        finally:
            loading_placeholder.empty()

            if data is None:
                st.markdown(f"""
                    <style>
                        @keyframes fadeIn {{
                            from {{ opacity: 0; transform: translateY(20px); }}
                            to {{ opacity: 1; transform: translateY(0); }}
                        }}
                        .fade-in {{
                            animation: fadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) forwards;
                        }}
                    </style>
                    <div class="fade-in" style="display: flex; flex-direction: column; align-items: center; margin: 80px auto 50px;">
                        <h2 style="margin: 40px 0 30px 0; padding-top: 20px;">Ошибка получения комментариев, попробуй ещё раз...</h2>
                        <div style="display: flex; gap: 20px; margin-bottom: 30px;">
                            <img src="{get_image_base64(mems[random.randint(0, 9)])}" width="500" style="opacity: 0; animation: fadeIn 0.8s 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;">
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            elif data.shape[0] != 0:
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    status_text.markdown(
                        '<div style="font-size: 15px; font-weight: bold;">Начало обработки данных...</div>',
                        unsafe_allow_html=True
                    )
                    data, data_for_model = prepare_data_for_model(data, "text")
                    progress_bar.progress(20)

                    status_text.markdown(
                        '<div style="font-size: 15px; font-weight: bold;">Анализ тональности комментариев...</div>',
                        unsafe_allow_html=True
                    )
                    data = get_data_with_predicted_label(data_for_model=data_for_model,
                                                         data=data,
                                                         path_to_model='sklearn-models/log_model.joblib',
                                                         column_with_text='text_prep')
                    progress_bar.progress(40)

                    status_text.markdown(
                        '<div style="font-size: 15px; font-weight: bold;">Подготовка данных для визуализации...</div>',
                        unsafe_allow_html=True
                    )

                    if data[data['predicted_label'] == 1].shape[0] > 0:
                        positive_comments = pd.Series((data[data['predicted_label'] == 1]
                                                       ['text_prep_stop_words'] + " ").sum().split()).value_counts().to_dict()
                    else:
                        positive_comments = {"позитивных комментариев нет": 1}

                    if data[data['predicted_label'] == 0].shape[0] > 0:
                        negative_comments = pd.Series((data[data['predicted_label'] == 0]
                                                       ['text_prep_stop_words'] + " ").sum().split()).value_counts().to_dict()
                    else:
                        negative_comments = {"негативных комментариев нет": 1}

                    progress_bar.progress(60)

                    status_text.markdown(
                        '<div style="font-size: 15px; font-weight: bold;">Генерация облаков слов...</div>',
                        unsafe_allow_html=True
                    )
                    wordcloud_positive = WordCloud(background_color="white",
                                                   colormap='Blues',
                                                   max_words=100,
                                                   width=1600,
                                                   height=1600).generate_from_frequencies(positive_comments)

                    wordcloud_negative = WordCloud(background_color="white",
                                                   colormap='Reds',
                                                   max_words=100,
                                                   width=1600,
                                                   height=1600).generate_from_frequencies(negative_comments)
                    progress_bar.progress(80)

                    status_text.markdown(
                        '<div style="font-size: 15px; font-weight: bold;">Построение графиков...</div>',
                        unsafe_allow_html=True
                    )

                    fig = plt.figure(figsize=(10, 7))

                    ax1 = fig.add_subplot(211)
                    ax2 = fig.add_subplot(223)
                    ax3 = fig.add_subplot(224)

                    if data[data['predicted_label'] == 1].shape[0] <= 0:
                        colors = ['#FC5A50']
                        labels = ['негативные']
                        startangle = 0
                    elif data[data['predicted_label'] == 0].shape[0] <= 0:
                        colors = ['#9ACD32']
                        labels = ['положительные']
                        startangle = 0
                    else:
                        colors=['#FC5A50', '#9ACD32']
                        labels=['негативные', 'положительные']
                        startangle = 90

                    ax1.pie(data['predicted_label'].value_counts(),
                            colors=colors,
                            labels=labels,
                            autopct='%1.1f%%',
                            startangle=startangle,
                            textprops={'fontsize': 14, 'color': 'black'},
                            wedgeprops={'linewidth': 1.5, 'edgecolor': 'white'})

                    ax2.imshow(wordcloud_positive, interpolation='bilinear')
                    ax2.axis('off')

                    ax3.imshow(wordcloud_negative, interpolation='bilinear')
                    ax3.axis('off')

                    ax2.set_title('Частые слова в позитивных комментариях', fontsize=14, pad=15, color='#000000')
                    ax3.set_title('Частые слова в негативных комментариях', fontsize=14, pad=15, color='#000000')

                    plt.tight_layout()
                    progress_bar.progress(100)

                finally:
                    progress_bar.empty()
                    status_text.empty()

                st.subheader('Результат:')

                st.pyplot(fig, clear_figure=True)
            else:
                st.markdown(f"""
                    <style>
                        @keyframes fadeIn {{
                            from {{ opacity: 0; transform: translateY(20px); }}
                            to {{ opacity: 1; transform: translateY(0); }}
                        }}
                        .fade-in {{
                            animation: fadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) forwards;
                        }}
                    </style>
                    <div class="fade-in" style="display: flex; flex-direction: column; align-items: center; margin: 80px auto 50px;">
                        <h2 style="margin: 40px 0 30px 0; padding-top: 20px;">Комментариев под видео ещё нет...</h2>
                        <div style="display: flex; gap: 20px; margin-bottom: 30px;">
                            <img src="{get_image_base64(mems[random.randint(0, 9)])}" width="500" style="opacity: 0; animation: fadeIn 0.8s 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;">
                        </div>
                    </div>
                    """, unsafe_allow_html=True)