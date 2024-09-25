# Standard library imports
import os
import time
import json
import secrets
import re
import urllib.parse
from datetime import datetime, timezone
import sqlite3

# Third-party library imports
import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session

# Application-specific imports
from api_calls import get_user_data, get_anime_data, update_rating_status
from recommendations_algorithm import recommend_animes
from database_calls import most_watched_genres_and_themes, genres_and_themes_top_5, get_anime_information, get_all_anime

# j+R6Nf@T8~n9Bsk
# TestUser69

load_dotenv()

CLIENT_ID = '8a50535b5e02e804f3091bc31256c0c7'
REDIRECT_URI = os.getenv('REDIRECT_URI')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TOKEN_URL = 'https://myanimelist.net/v1/oauth2/token'
API_BASE_URL = 'https://api.myanimelist.net/v2/'

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = os.urandom(24)
Session(app)

def get_code_verifier () -> str:
    return secrets.token_urlsafe(100)[:128]

def generate_state() -> str:
    return secrets.token_urlsafe(16)

def is_token_expired() -> bool:
    return time.time() >= session.get('expires_at', 0)

def refresh_token() -> None:
    token_url = 'https://myanimelist.net/v1/oauth2/token'

    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': session.get('refresh_token'),
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    
    response = requests.post(token_url, data=payload)
    
    if response.status_code == 200:
        token_data = response.json()
        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data.get('refresh_token') 
        session['expires_at'] = time.time() + token_data['expires_in']
    else:
        session.pop('access_token', None)
        session.pop('refresh_token', None)
        session.pop('expires_at', None)
        return render_template('error.html', error='Could not refresh token. 401')

def anime_exists(anime_id, anime_list):
    statuses = ['completed', 'watching', 'plan_to_watch', 'dropped', 'on_hold']
    for status in statuses:
        if any(anime['node']['id'] == int(anime_id) for anime in anime_list.get(status, {}).get('data', [])):
            return True
    return False

@app.route('/')
def index():
    if is_token_expired():
        refresh_token()
    if 'access_token' in session:
        return redirect(url_for('profile')) 
        
    code_verifier = code_challenge = get_code_verifier()
    
    STATE = generate_state()

    session['code_verifier'] = code_verifier
    session['oauth_state'] = STATE

    base_url = 'https://myanimelist.net/v1/oauth2/authorize'
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID, 
        'code_challenge': code_challenge,
        'state': STATE,
        'redirect_uri': REDIRECT_URI,   
    }

    authorization_url = f"{base_url}?{urllib.parse.urlencode(params)}"

    if 'new_user_id' in session:
        return redirect(authorization_url)
    else:
        return render_template('login.html', url=authorization_url)


@app.route('/guide')
def guide():
    return render_template('guide.html')


@app.route('/callback')
def callback():
    code = request.args.get('code')
    received_state = request.args.get('state')
    code_verifier = session.get('code_verifier')

    if received_state != session.get('oauth_state'):
        error = 'Invalid state parameter. 400'
        return render_template('error.html', error=error)
    if not code_verifier:
        error = 'No code verifier. 400'
        return render_template('error.html', error=error) 
    
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,           
        'code_verifier': code_verifier,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
    }

    response = requests.post(TOKEN_URL, data=payload)

    if response.status_code == 200:
        token_data = response.json()
        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data['refresh_token']
        session['expires_at'] = time.time() + token_data['expires_in']
 
        return redirect(url_for('profile'))   
    else:
        error = 'Could not access token. 401'
        return render_template('error.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'new_user_id' in session:
            session.pop('new_user_id', None)

        return render_template('login.html')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('database/users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, password_hash FROM Users WHERE username = ?", (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user[1], password):
            session['new_user_id'] = user[0]

            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        

@app.route('/logout')
def logout():
    session.pop('new_user_id', None)
    return redirect(url_for('index'))


@app.route('/logout_mal')                                               
def logout_mal():                                                      
    session.pop('access_token', None)                                   
    session.pop('refresh_token', None)
    session.pop('expires_at', None)
    session.pop('animelist', None)
    session.pop('recommendations_animes', None)
    session.pop('recommendations_movies', None)
    session.pop('user_data', None)
    session.pop('top_5', None)

    return redirect(url_for('index'))


@app.route('/rate', methods=['GET', 'POST'])
def rate():
    if 'access_token' not in session:
        return redirect(url_for('index'))
    
    anime_list = session.get('animelist', {})

    if request.method == 'GET':
        completed_animes = anime_list.get('completed', {}).get('data', [])
        unrated_anime_ids = [anime['node']['id'] for anime in completed_animes if anime['list_status']['score'] == 0]
        
        tuples_list = [(anime_id, 0) for anime_id in unrated_anime_ids]

        if tuples_list == []:
            return render_template('rate.html', animes=[])
        
        anime_information = get_anime_information(tuples_list)
        return render_template('rate.html', animes=anime_information)

    if request.method == 'POST':
        anime_ids = request.form.getlist('anime_ids')
        is_updated = request.form.get('check-update', 'unchecked') 

        for anime_id in anime_ids:
            rating = request.form.get(f'rating-{anime_id}', None)
            status = request.form.get(f'status-{anime_id}', None)
 
            updated_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00') if is_updated == 'checked' else ''   

            if not anime_exists(anime_id, anime_list):
                if rating and status:
                    update_rating_status(anime_id, rating, status)

                    anime_list.setdefault('completed', {'data': []})
                    anime_list['completed']['data'].append({
                        'node': {'id': int(anime_id)},
                        'list_status': {'status': status, 'score': int(rating), 'updated_at': updated_at}
                    })

            elif rating and status:
                update_rating_status(anime_id, rating, status)

                for anime in anime_list['completed'].get('data', []):
                    if anime['node']['id'] == int(anime_id):
                        anime['list_status']['score'] = int(rating)
                        anime['list_status']['status'] = status
                        anime['list_status']['updated_at'] = updated_at
                        break
            
            elif rating and rating != '0':
                update_rating_status(anime_id, rating, 'completed')

                for anime in anime_list['completed'].get('data', []):
                    if anime['node']['id'] == int(anime_id):
                        anime['list_status']['score'] = int(rating)
                        anime['list_status']['status'] = 'completed'
                        anime['list_status']['updated_at'] = updated_at
                        break
        
        session['animelist'] = anime_list
        
        return jsonify({'message': 'Anime list updated successfully'})


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').lower()
    check_list = request.args.get('check_list', 'off')

    if len(query) > 100:
        return jsonify([])
    if not query:
        return jsonify([])

    all_animes = get_all_anime()
    matching_animes = [] 

    watched_anime_ids = set()
    anime_list = session.get('animelist', {})

    for status in ['completed', 'watching', 'on_hold', 'dropped', 'plan_to_watch']:
        watched_anime_ids.update(
            anime['node']['id'] for anime in anime_list.get(status, {}).get('data', [])
        )

    # Regex patterns for filters and sorting
    patterns = {
        'studio': re.compile(r'studio:([\w\s]+)', re.IGNORECASE),
        'score': re.compile(r'score:(>|>=|<|<=)?(\d+)', re.IGNORECASE),
        'episodes': re.compile(r'episodes:(\d+)', re.IGNORECASE),
        'year': re.compile(r'year:(\d+)', re.IGNORECASE),
        'id': re.compile(r'id:(\d+)', re.IGNORECASE),
        'sort': re.compile(r'(asc|desc):(scores|year)', re.IGNORECASE)  # Sorting regex
    }

    # Filters
    studio_filter = patterns['studio'].search(query)
    score_filter = patterns['score'].search(query)
    episodes_filter = patterns['episodes'].search(query)
    year_filter = patterns['year'].search(query)
    id_filter = patterns['id'].search(query)
    sort_filter = patterns['sort'].search(query)  

    query = re.sub(r'(asc|desc):(scores|year)', '', query).strip()

    main_query = re.sub(r'(studio:[\w\s]+|score:(>|>=|<|<=)?\d+|episodes:\d+|year:\d+|id:\d+)', '', query).strip()
    normalized_query = re.sub(r'\W+', '', main_query)

    for anime_id, anime in all_animes.items():
        title_default = str(anime.get('title_default', '')).lower()
        title_english = str(anime.get('title_english', '')).lower()

        normalized_title_default = re.sub(r'\W+', '', title_default)
        normalized_title_english = re.sub(r'\W+', '', title_english)

        if anime_id in watched_anime_ids and check_list == 'on':
            continue

        if id_filter:
            id_query = int(id_filter.group(1))
            if anime_id != id_query:
                continue

        if not id_filter and main_query and not (
            query == str(anime_id) or 
            main_query in title_default or 
            main_query in title_english or 
            normalized_query in normalized_title_default or 
            normalized_query in normalized_title_english
        ):
            continue
        
        if studio_filter:
            studio_query = studio_filter.group(1).lower().strip()
            studio_name = anime.get('studio', '') or ''
            studio_name = studio_name.lower().strip()
            if studio_query not in studio_name:
                continue
        
        if score_filter:
            operator = score_filter.group(1)
            score_query = int(score_filter.group(2))
            anime_score = anime.get('score')
            if anime_score is None:
                continue
            anime_score = int(anime_score)

            if operator == '>':
                if anime_score <= score_query:
                    continue
            elif operator == '>=':
                if anime_score < score_query:
                    continue
            elif operator == '<':
                if anime_score >= score_query:
                    continue
            elif operator == '<=':
                if anime_score > score_query:
                    continue
            elif anime_score != score_query:
                continue

        if episodes_filter:
            episodes_query = int(episodes_filter.group(1))
            if anime.get('episodes') is None or int(anime.get('episodes')) != episodes_query:
                continue

        if year_filter:
            year_query = int(year_filter.group(1))
            if anime.get('year') is None or int(anime.get('year')) != year_query:
                continue

        matching_animes.append({'id': anime_id, **anime})

    if sort_filter:
        sort_order = sort_filter.group(1).lower()
        sort_field = sort_filter.group(2).lower()
        
        reverse_order = (sort_order == 'desc')

        if sort_field == 'scores':
            matching_animes.sort(
                key=lambda x: x.get('score') if x.get('score') is not None else 0,
                reverse=reverse_order
            )
        elif sort_field == 'year':
            matching_animes.sort(
                key=lambda x: x.get('year') if x.get('year') is not None else 0,
                reverse=reverse_order
            )

    limited_animes = matching_animes[:50]

    return jsonify(limited_animes)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))

        # Check if username already exists
        with sqlite3.connect('database/users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM Users WHERE username = ?", (username,))
            if cursor.fetchone():
                flash('Username already exists', 'danger')
                return redirect(url_for('register'))

            # Insert new user
            password_hash = generate_password_hash(password)
            cursor.execute("INSERT INTO Users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()

            cursor.execute("SELECT user_id FROM Users WHERE username = ?", (username,))
            session['new_user_id'] = cursor.fetchone()[0]

        return redirect(url_for('profile'))

    return render_template('register.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():  
    if 'access_token' not in session:
        return redirect(url_for('index'))
    
    access_token = session.get('access_token')

    if request.method == 'GET':
        try:    
            if 'animelist' not in session:
                user_animelist = get_anime_data(access_token)
                session['animelist'] = user_animelist
            
            if 'user_data' not in session:
                user_data = get_user_data(access_token)
                session['user_data'] = user_data
            
            if 'top_5' not in session:
                GenresThemesCompleted = most_watched_genres_and_themes(session['animelist'])
                session['top_5'] = genres_and_themes_top_5(GenresThemesCompleted)
            
            if 'recommendations_animes' not in session or 'recommendations_movies' not in session:
                recommendations = recommend_animes(session['animelist'])
                session['recommendations_animes'] = get_anime_information(recommendations['regular'])
                session['recommendations_movies'] = get_anime_information(recommendations['movies'])
                
            user_data = session['user_data']
            top_5 = session['top_5']
            animes = session['recommendations_animes']
            movies = session['recommendations_movies']

        except ValueError as e:
            return render_template('error.html', error=str(e))

        user_id = session.get('new_user_id', None)

        return render_template('profile.html', 
                            user_data=user_data, 
                            stats=top_5, 
                            animes=animes, 
                            movies=movies,
                            user_id=user_id
                            )

    if request.method == 'POST':
        allow_hentai = request.form.get('include_hentai')
        allow_hentai = True if allow_hentai == 'true' else False

        if request.form.get('user_ids', None) is not None:
            if session.get('new_user_id') is None:
                return render_template('error.html', error="Please login first.")
            
            user_id_input = request.form['user_ids']

            if user_id_input and re.fullmatch(r'^\d+(\s*,\s*\d+)*$', user_id_input):
                user_ids = [id.strip() for id in user_id_input.split(',')]
                if len(user_ids) > 10:
                    return render_template('error.html', error="Invalid input. Please enter no more than 10 user IDs.")
                
                if session.get('new_user_id') not in user_ids:
                    user_ids.append(session.get('new_user_id'))
            else:
                return render_template('error.html', error="Invalid input. Please enter only numbers separated by commas.")

            combined_anime_list = {
                'completed': {'data': [], 'paging': {}},
                'watching': {'data': [], 'paging': {}},
                'on_hold': {'data': [], 'paging': {}},
                'plan_to_watch': {'data': [], 'paging': {}},
                'dropped': {'data': [], 'paging': {}}
            }
            for user_id in user_ids:
                user_id = int(user_id)

                if user_id is not None:
                    with sqlite3.connect('database/users.db') as conn:
                        cursor = conn.cursor()

                        cursor.execute("SELECT anime_list FROM UserAnimeList WHERE user_id = ?", (user_id,))
                        anime_list = cursor.fetchone()

                        if anime_list:
                            anime_list = json.loads(anime_list[0])

                            # Merge the lists
                            for status in combined_anime_list.keys():
                                if status in anime_list and 'data' in anime_list[status]:
                                    combined_anime_list[status]['data'].extend(anime_list[status]['data'])
                        else:
                            continue

            for status in combined_anime_list.keys():
                seen_ids = set()
                unique_data = []
                for entry in combined_anime_list[status]['data']:
                    anime_id = entry['node']['id']
                    if anime_id not in seen_ids:
                        seen_ids.add(anime_id)
                        unique_data.append(entry)

                combined_anime_list[status]['data'] = unique_data

            recommendations = recommend_animes(combined_anime_list, 40, allow_hentai)
            animes = get_anime_information(recommendations['regular'])  
            movies = get_anime_information(recommendations['movies'])

        elif request.form.get('limit', None) is not None:
            limit = int(request.form['limit'])

            user_animelist = session['animelist']
            recommendations = recommend_animes(user_animelist, limit, allow_hentai)

            animes = get_anime_information(recommendations['regular'])  
            movies = get_anime_information(recommendations['movies'])

            session['recommendations_animes'] = animes
            session['recommendations_movies'] = movies
        
        elif request.form.get('update', None) is not None:
            
            user_animelist = get_anime_data(access_token)
            user_data = get_user_data(access_token)

            recommendations = recommend_animes(user_animelist, 0, allow_hentai)

            animes = get_anime_information(recommendations['regular'])  
            movies = get_anime_information(recommendations['movies'])

            session['recommendations_animes'] = animes
            session['recommendations_movies'] = movies

            session['animelist'] = user_animelist
            session['user_data'] = user_data

            GenresThemesCompleted = most_watched_genres_and_themes(user_animelist)
            top_5 = genres_and_themes_top_5(GenresThemesCompleted)

            session['top_5'] = top_5	

            if 'new_user_id' in session:
                user_animelist_json = json.dumps(user_animelist, sort_keys=True)
                user_id = session['new_user_id']

                with sqlite3.connect('database/users.db') as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        SELECT anime_list
                        FROM UserAnimeList
                        WHERE user_id = ?
                    """, (user_id,  ))
                    
                    result = cursor.fetchone()

                    if result:
                        user_animelist_db = result[0]
                        user_animelist_db_json = json.dumps(json.loads(user_animelist_db), sort_keys=True)
                        
                        # Update the database if the anime lists are different
                        if user_animelist_json != user_animelist_db_json:
                            cursor.execute("""
                                UPDATE UserAnimeList 
                                SET anime_list = ? 
                                WHERE user_id = ?
                            """, (user_animelist_json, user_id))
                            conn.commit()
                    else:
                        # Insert a new record if it doesn't exist
                        cursor.execute("""
                            INSERT INTO UserAnimeList (user_id, anime_list) 
                            VALUES (?, ?)
                        """, (user_id, user_animelist_json))
                        conn.commit()

        elif request.form.get('select', None) is not None:
            input = request.form['select']

            if input and re.fullmatch(r'^\d+(\s*,\s*\d+)*$', input):
                anime_ids = [int(id.strip()) for id in input.split(',')]
                if len(anime_ids) > 150:
                    return render_template('error.html', error="Invalid input. Please enter no more than 150 anime IDs")
            else:
                return render_template('error.html', error="Invalid input. Please enter only anime IDs separated by commas.")
            
            completed_data = []
            for anime_id in anime_ids:
                anime_entry = {
                    "node": {
                        "id": anime_id
                    },
                    "list_status": {
                        "status": "completed",
                        "score": 10,
                    }
                }
                completed_data.append(anime_entry)

            response_data = {
                "completed": {
                    "data": completed_data,
                },
            }
                
            recommendations = recommend_animes(response_data, None, allow_hentai)
    
            filtered_regular_recommendations = [
                (anime_id, similarity) for anime_id, similarity in recommendations.get('regular', [])
                if anime_id not in anime_ids
            ]
            
            filtered_movie_recommendations = [
                (anime_id, similarity) for anime_id, similarity in recommendations.get('movies', [])
                if anime_id not in anime_ids
            ]
            
            animes = get_anime_information(filtered_regular_recommendations)
            movies = get_anime_information(filtered_movie_recommendations)

            session['recommendations_animes'] = animes
            session['recommendations_movies'] = movies
    
        user_data = session.get('user_data', None)  
        top_5 = session.get('top_5', None)
        user_id = session.get('new_user_id', None)

        return render_template('profile.html', 
                    user_data=user_data, 
                    stats=top_5, 
                    animes=animes, 
                    movies=movies,
                    user_id=user_id
                    )      
    