import requests
from flask import session
import time
import sqlite3

API_BASE_URL = 'https://api.myanimelist.net/v2/'

def get_user_data(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    fields = {'fields': 'id,name,anime_statistics'}
    response_user = requests.get(f'{API_BASE_URL}users/@me', headers=headers, params=fields)

    if response_user.status_code == 200:
        user_data = response_user.json()
        session['user_id'] = user_data['id']
    else:   
        raise ValueError('Could not access user data. Status code: {}'.format(response_user.status_code))
    
    return user_data
    
def get_anime_data(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    statuses = ['completed', 'watching', 'on_hold', 'dropped', 'plan_to_watch']
    anime_data = {}

    for status in statuses:
        params = {
            'fields': 'list_status',
            'status': status,
            'limit': 1000,
            'sort': 'list_score',
            'nsfw': 'true',
        }

        response_anime = requests.get(f'{API_BASE_URL}users/@me/animelist', headers=headers, params=params)
        if response_anime.status_code == 200:
            anime_data[status] = response_anime.json()
            time.sleep(0.3)
        else:
            raise ValueError('Could not access anime data. Status code: {}'.format(response_anime.status_code))
    
    return anime_data

def update_rating_status(anime_id, rating, status):

    with sqlite3.connect('database/animes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT episodes FROM Animes WHERE id = ?", (anime_id,))
        episodes = cursor.fetchone()[0]

        num_watched_episodes = episodes if status == 'completed' else 0
        cursor.close()


    url = f'https://api.myanimelist.net/v2/anime/{anime_id}/my_list_status'
    headers = {
        'Authorization': f'Bearer {session["access_token"]}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'status': status,
        'score': int(rating),
        'num_watched_episodes': int(num_watched_episodes)
    }
        
    response = requests.put(url, headers=headers, data=data)
    if response.status_code == 200:
        print("Anime list updated successfully")
    else:
        print(f"Failed to update anime list: {response.status_code} - {response.text}")
