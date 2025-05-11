import requests
import json
import pandas as pd
import numpy as np

def get_video_id(url):
    video_id = url[:-1].split("/")[-1]
    return video_id

def create_comments_df(comments) -> pd.DataFrame:
    if not comments:
        return pd.DataFrame()

    df = pd.json_normalize(
        comments,
        meta=[
            'id', 'text', 'video_id', 'created_ts',
            'likes_number', 'dislikes_number', 'replies_number'
        ],
        meta_prefix='comment_',
        sep='_'
    )

    df = df[[
        'id', 'text', 'video_id', 'created_ts',
        'likes_number', 'dislikes_number', 'replies_number'
    ]]

    return df

def fetch_comments(video_url):
    df = pd.DataFrame()
    video_id = get_video_id(video_url)
    url = f"https://rutube.ru/api/v2/comments/video/{video_id}/?client=wdp&sort_by=popular"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        has_next = data.get('has_next', False)
        df = create_comments_df(data.get('results', []))

        while has_next:
            last_comment_id = df.iloc[-1]['id']
            has_next, next_df = get_next_comments(video_id, last_comment_id)

            df = pd.concat([df, next_df], axis=0)

        df.index = np.arange(df.shape[0])
        answers_df = get_comments_answers(df)
        finally_df = pd.concat([df, answers_df], axis=0)
        finally_df.index = np.arange(finally_df.shape[0])

        return finally_df
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return []
    except json.JSONDecodeError:
        print("Ошибка обработки JSON-ответа")
        return []

def get_next_comments(video, comment_id, parent_id=None):
    if parent_id is not None:
        url = f"https://rutube.ru/api/v2/comments/video/{video}/?client=wdp&direction=earliest&comment_id={comment_id}&parent_id={parent_id}"
    else:
        url = f"https://rutube.ru/api/v2/comments/video/{video}/?client=wdp&direction=earliest&comment_id={comment_id}&sort_by=popular"

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    has_next = data.get('has_next', False)

    return has_next, create_comments_df(data.get('results', []))

def get_comments_answers(comments_data):
    data_with_answers = comments_data[comments_data['replies_number'] > 0]
    answers_df = pd.DataFrame()

    for row in data_with_answers.itertuples():
        url = f"https://rutube.ru/api/v2/comments/video/{row.video_id}?client=wdp&parent_id={row.id}&limit=10"

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        has_next = data.get('has_next', False)
        df = create_comments_df(data.get('results', []))

        while has_next:
            last_comment_id = df.iloc[-1]['id']
            has_next, next_df = get_next_comments(row.video_id, last_comment_id, row.id)

            df = pd.concat([df, next_df], axis=0)

        answers_df = pd.concat([df, answers_df], axis=0)

    return answers_df