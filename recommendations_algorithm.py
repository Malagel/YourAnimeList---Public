from scipy.spatial.distance import cosine
from collections import Counter
import numpy as np
import sqlite3
import json



def get_anime_ids(user_data):
    completed_anime_ids = [anime['node']['id'] for anime in user_data.get('completed', {}).get('data', [])]
    dropped_anime_ids = [anime['node']['id'] for anime in user_data.get('dropped', {}).get('data', [])]
    watching_anime_ids = [anime['node']['id'] for anime in user_data.get('watching', {}).get('data', [])]
    on_hold_anime_ids = [anime['node']['id'] for anime in user_data.get('on_hold', {}).get('data', [])]

    anime_ids = set(completed_anime_ids + dropped_anime_ids + watching_anime_ids + on_hold_anime_ids)

    return anime_ids


def get_user_data_preferences(user_data, db_path='database/animes.db', recent_limit=None):
    user_preferences = {
        'genre': Counter(),
        'theme': Counter(), 
        'studio': Counter(), 
        'demographics': Counter(), 
        'episodes': [], 
        'year': []
    }

    completed_animes = user_data.get('completed', {}).get('data', [])

    completed_animes.sort(key=lambda x: x['list_status'].get('updated_at', ''), reverse=True)

    if recent_limit == 0:
        recent_limit = None
        
    if recent_limit is not None:
        completed_animes = completed_animes[:recent_limit]

    completed_anime_ids = [anime['node']['id'] for anime in completed_animes]
    completed_scores = {anime['node']['id']: anime['list_status']['score'] for anime in completed_animes}

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        for anime_id in completed_anime_ids:
            cursor.execute("""
                SELECT genre_vector, theme_vector, studio_id, episodes, year, demographic_id
                FROM AnimeVectors
                LEFT JOIN AnimeStudios ON AnimeVectors.anime_id = AnimeStudios.anime_id
                LEFT JOIN Animes ON AnimeVectors.anime_id = Animes.id
                LEFT JOIN AnimeDemographics ON AnimeVectors.anime_id = AnimeDemographics.anime_id
                WHERE AnimeVectors.anime_id = ?
            """, (anime_id,))
            result = cursor.fetchone()
            if result:
                genre_vector_str, theme_vector_str, studio_id, episodes, year, demographic_id = result

                genre_vector = np.array(list(map(int, genre_vector_str.split(',')))) if genre_vector_str else np.zeros(1)
                theme_vector = np.array(list(map(int, theme_vector_str.split(',')))) if theme_vector_str else np.zeros(1)

                score = completed_scores.get(anime_id, 1)

                user_preferences['genre'] += Counter(dict(zip(range(len(genre_vector)), genre_vector * score)))
                user_preferences['theme'] += Counter(dict(zip(range(len(theme_vector)), theme_vector * score)))

                if studio_id:
                    user_preferences['studio'][studio_id] += 1
                if demographic_id:
                    user_preferences['demographics'][demographic_id] += 1
                if episodes:
                    user_preferences['episodes'].append(episodes)
                if year:
                    user_preferences['year'].append(year)

    # Calculate average episodes and year for user preferences
    if user_preferences['episodes']:
        user_preferences['episodes'] = sum(user_preferences['episodes']) / len(user_preferences['episodes'])
    else:
        user_preferences['episodes'] = None

    if user_preferences['year']:
        user_preferences['year'] = sum(user_preferences['year']) / len(user_preferences['year'])
    else:
        user_preferences['year'] = None

    return user_preferences



def compute_user_preferences(user_preferences, db_path='database/animes.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Genres")
        num_genres = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Themes")
        num_themes = cursor.fetchone()[0]

    genre_vector = np.array([user_preferences['genre'].get(i, 0) for i in range(num_genres)])
    theme_vector = np.array([user_preferences['theme'].get(i, 0) for i in range(num_themes)])

    return genre_vector, theme_vector



def recommend_animes(user_data, recent_limit=None, hentai=False, top_n=64, db_path='database/animes.db'):
    # recent_limit is the limit of the data that will serve as input for the algorithm. if it's None, all data will be used.
    # top_n is the number of recommendations that will be returned
    excluded_anime_ids = get_anime_ids(user_data)
    excluded_anime_types = ['CM', 'PV', 'Music', 'Special', 'TV Special']

    user_preferences = get_user_data_preferences(user_data, db_path, recent_limit)
    genre_vector, theme_vector = compute_user_preferences(user_preferences, db_path)

    recommendations = []
    recommendations_movies = [] 

    added_anime_ids = set()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Base SQL query
        query = """
            SELECT a.id, a.score, a.episodes, a.year, av.genre_vector, av.theme_vector, s.id, t.name, d.id
            FROM Animes a
            JOIN AnimeVectors av ON a.id = av.anime_id
            LEFT JOIN AnimeStudios ans ON a.id = ans.anime_id
            LEFT JOIN Studios s ON ans.studio_id = s.id
            LEFT JOIN AnimeTypes ant ON a.id = ant.anime_id
            LEFT JOIN Types t ON ant.type_id = t.id
            LEFT JOIN AnimeDemographics ad ON a.id = ad.anime_id
            LEFT JOIN Demographics d ON ad.demographic_id = d.id
        """
        
        if not hentai:
            query += " WHERE NOT EXISTS (SELECT 1 FROM AnimeGenres ag WHERE ag.anime_id = a.id AND ag.genre_id = ?)"
        
        if not hentai:
            cursor.execute(query, (12,))  
        else:
            cursor.execute(query)  
            
        for row in cursor.fetchall():
            anime_id, score, episodes, year, genre_vector_str, theme_vector_str, studio_id, anime_type, demographic_id = row
            if anime_id in excluded_anime_ids:
                continue  
            if anime_type in excluded_anime_types:
                continue

            genre_vector_db = np.array(list(map(int, genre_vector_str.split(','))))
            theme_vector_db = np.array(list(map(int, theme_vector_str.split(','))))
            
            if len(genre_vector_db) != len(genre_vector) or len(theme_vector_db) != len(theme_vector):
                continue
            
            genre_similarity = 1 - cosine(genre_vector, genre_vector_db)
            theme_similarity = 1 - cosine(theme_vector, theme_vector_db)

            if score is None:
                continue

            if np.isnan(genre_similarity) or np.isnan(theme_similarity):
                continue  
            else:
                similarity = ((genre_similarity + theme_similarity) / 2) * (score / 10)

            # Add Weights

            if year and user_preferences['year']:
                year_difference = abs(year - user_preferences['year'])
                year_similarity = 1 - (year_difference / max(year, user_preferences['year']))
                year_weight = 1.5 
                similarity *= (1 + (year_similarity - 1) * year_weight)

            if studio_id:
                studio_weight = user_preferences['studio'][studio_id] if studio_id in user_preferences['studio'] else 0
                max_studio_weight = max(user_preferences['studio'].values()) if user_preferences['studio'] else 1
                studio_similarity = studio_weight / max_studio_weight
                similarity *= (0.8 + 0.3 * studio_similarity)

            if demographic_id:
                demographic_weight = user_preferences['demographics'][demographic_id] if demographic_id in user_preferences['demographics'] else 0
                max_demographic_weight = max(user_preferences['demographics'].values()) if user_preferences['demographics'] else 1
                demographic_similarity = demographic_weight / max_demographic_weight
                similarity *= (0.8 + 0.4 * demographic_similarity)

            # Add movie before episodes weight (because it doesn't make sense after)

            if anime_type == 'Movie':
                if anime_id not in added_anime_ids:  
                    added_anime_ids.add(anime_id)  
                    recommendations_movies.append((anime_id, similarity))
                continue

            if episodes and user_preferences['episodes']:
                episode_similarity = 1 - abs(episodes - user_preferences['episodes']) / max(episodes, user_preferences['episodes'])
                similarity *= episode_similarity

            if anime_id not in added_anime_ids:  
                recommendations.append((anime_id, similarity))
                added_anime_ids.add(anime_id) 
    
    recommendations.sort(key=lambda x: x[1], reverse=True)
    recommendations_movies.sort(key=lambda x: x[1], reverse=True)
    
    return {
        'regular': recommendations[:top_n],
        'movies': recommendations_movies[:top_n]
    }