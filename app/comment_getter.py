import requests
import json
import pandas as pd
import numpy as np
import time
import os
import random
from datetime import datetime
import joblib

def get_video_id(url):
    if url[-1] == '/':
        video_id = url[:-1].split("/")[-1]
    else:
        video_id = url.split("/")[-1]
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

def get_rutube_comments(video_url):
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
        return None
    except json.JSONDecodeError:
        print("Ошибка обработки JSON-ответа")
        return None

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
    answers_df = pd.DataFrame()

    if comments_data.shape[0] != 0:
        data_with_answers = comments_data[comments_data['replies_number'] > 0]

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

def get_info_from_vk_url(url):
    return url[url.rfind('video')+5:].split("_")[::-1]

def get_vk_comments(url, version, client_id, client_secret, app_id, delay=1.0):
    video_id, owner_id = get_info_from_vk_url(url)
    url = f"https://api.vkvideo.ru/method/video.getComments?v={version}&client_id={client_id}"
    try:
        token = joblib.load("tokens/vk_token.joblib")
    except:
        get_vk_anon_token(client_id, client_secret, app_id)
        token = joblib.load("tokens/vk_token.joblib")

    df = pd.DataFrame()

    params = {
        "video_id": video_id,
        "owner_id": owner_id,
        "count": "20",
        "offset": "0",
        "need_likes": "1",
        "extended": "1",
        "fields": "photo_100,first_name_dat",
        "access_token": token
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    try:
        while int(params['offset']) < int(data['response']['count']):
            if "error" in data:
                print(f"API Error {data['error']['error_code']}: {data['error']['error_msg']}")
                return pd.DataFrame()

            if "response" not in data:
                print("Ошибка в ответе API:", data)
                return pd.DataFrame()

            comments = data["response"]["items"]
            video_id = params["video_id"]

            comments_list = []
            for comment in comments:
                comment_data = {
                    "id": comment["id"],
                    "text": comment["text"],
                    "video_id": video_id,
                    "created_ts": datetime.fromtimestamp(comment["date"]),
                    "dislikes_number": 0,
                    "replies_number": comment.get("thread", {}).get("count", 0)
                }

                try:
                    if comment["deleted"]:
                        comment_data['likes_number'] = -1000
                except:
                    comment_data['likes_number'] = comment['likes']['count']
                comments_list.append(comment_data)

            df = pd.concat([df, pd.DataFrame(comments_list)], axis=0)
            params['offset'] = str(int(params['offset']) + int(params['count']))
            time.sleep(0.5 + random.uniform(0, delay))

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        try:
            answers_df = get_comments_answers_vk(df, params, client_id, version)

            finally_df = pd.concat([df, answers_df], axis=0)
            finally_df.index = np.arange(finally_df.shape[0])
        except:
            return pd.DataFrame()

        return finally_df
    except requests.exceptions.RequestException as e:
        print("Ошибка при выполнении запроса:", e)
        return None
    except (ValueError, KeyError) as e:
        try:
            if data['error']['error_msg'] == 'Anonymous token has expired':
                get_vk_anon_token(client_id, client_secret, app_id)
            return None
        except (ValueError, KeyError) as e:
            print("Ошибка обработки данных:", e)
            return None

def get_comments_answers_vk(comment_data, params, client_id, version, delay=1.0):
    data_with_answers = comment_data[comment_data['replies_number'] > 0]
    answers_df = pd.DataFrame()

    for row in data_with_answers.itertuples():
        url = f"https://api.vkvideo.ru/method/video.getComments?v={version}&client_id={client_id}"

        params['offset'] = "0"
        params['comment_id'] = row.id
        df = pd.DataFrame()

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        while int(params['offset']) < int(data['response']['count']):
            comments = data["response"]["items"]
            video_id = params["video_id"]

            comments_list = []
            for comment in comments:
                comment_data = {
                    "id": comment["id"],
                    "text": comment["text"],
                    "video_id": video_id,
                    "created_ts": datetime.fromtimestamp(comment["date"]),
                    "dislikes_number": 0,
                    "replies_number": comment.get("thread", {}).get("count", 0)
                }

                try:
                    if comment["deleted"]:
                        comment_data['likes_number'] = -1000
                except:
                    comment_data['likes_number'] = comment['likes']['count']
                comments_list.append(comment_data)

            df = pd.concat([df, pd.DataFrame(comments_list)], axis=0)
            params['offset'] = str(int(params['offset']) + int(params['count']))
            time.sleep(0.5 + random.uniform(0, delay))

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        answers_df = pd.concat([df, answers_df], axis=0)

    return answers_df

def get_vk_anon_token(client_id, client_secret, app_id):
    try:
        os.mkdir("tokens")
    except:
        print("dir exist")
    url = "https://login.vk.com/?act=get_anonym_token"

    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": "audio_anonymous,video_anonymous,photos_anonymous,profile_anonymous",
        "isApiOauthAnonymEnabled": "false",
        "version": 1,
        "app_id": app_id,
    }

    try:
        response = requests.post(
            url,
            data=params
        )
        response.raise_for_status()

        data = response.json()
        data = data.get('data', "").get("access_token", "")

        joblib.dump(data, "tokens/vk_token.joblib")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {str(e)}")
    except ValueError as e:
        print("Ошибка парсинга JSON:", e)