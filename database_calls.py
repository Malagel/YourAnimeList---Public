import sqlite3
from collections import Counter

def most_watched_genres_and_themes(user_data, db_path='database/animes.db'):
    completed_data = user_data.get('completed', {}).get('data', [])
    anime_ids = [anime['node']['id'] for anime in completed_data]
    
    if not anime_ids:
        return {'genres': {}, 'themes': {}}
        
    anime_ids_tuple = tuple(anime_ids)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Query for genres
        cursor.execute("""
            SELECT g.name
            FROM AnimeGenres ag
            JOIN Genres g ON ag.genre_id = g.id
            WHERE ag.anime_id IN (""" + ','.join('?' * len(anime_ids)) + """)
        """, anime_ids_tuple)
        genres = cursor.fetchall()

        # Query for themes
        cursor.execute("""
            SELECT t.name
            FROM AnimeThemes at
            JOIN Themes t ON at.theme_id = t.id
            WHERE at.anime_id IN (""" + ','.join('?' * len(anime_ids)) + """)
        """, anime_ids_tuple)
        themes = cursor.fetchall()
    
        genre_counts = Counter(genre[0] for genre in genres)
        theme_counts = Counter(theme[0] for theme in themes)
    
    sorted_genres = dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True))
    sorted_themes = dict(sorted(theme_counts.items(), key=lambda x: x[1], reverse=True))
    
    return {'genres': sorted_genres, 'themes': sorted_themes}

def genres_and_themes_top_5(stats): 
    
    top_genres = list(stats['genres'].items())[:5]
    top_themes = list(stats['themes'].items())[:5]

    return {
        'genres': top_genres,
        'themes': top_themes
    }

def get_anime_information(recommendations, db_path='database/animes.db'):
    anime_info_dict = {}

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        for anime_id, similarity_score in recommendations:
            cursor.execute("""
                SELECT a.name, a.english_name, a.year, a.episodes, a.score, a.image, s.name
                FROM Animes a
                LEFT JOIN AnimeStudios ans ON a.id = ans.anime_id 
                LEFT JOIN Studios s ON ans.studio_id = s.id
                WHERE a.id = ?
            """, (anime_id,)) 
            anime_info = cursor.fetchone()

            if anime_info:
                # adds the english title if it exists (adding this because I forget)
                title = anime_info[1] if anime_info[1] else anime_info[0]

                anime_info_dict[anime_id] = {
                    'title': title,
                    'year': anime_info[2],
                    'episodes': anime_info[3],
                    'score': anime_info[4],
                    'image': anime_info[5],
                    'studio': anime_info[6],
                    'similarity': similarity_score
                }
    
    return anime_info_dict

def get_all_anime(db_path='database/animes.db'):
    anime_info_dict = {}

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id 
            FROM Animes
        """)
        all_anime_ids = cursor.fetchall()

        for anime_id in all_anime_ids:
            anime_id = anime_id[0]

            cursor.execute("""
                SELECT a.name, a.english_name, a.year, a.episodes, a.score, a.image, s.name
                FROM Animes a
                LEFT JOIN AnimeStudios ans ON a.id = ans.anime_id 
                LEFT JOIN Studios s ON ans.studio_id = s.id
                WHERE a.id = ?
            """, (anime_id,)) 
            anime_info = cursor.fetchone()

            title_display = anime_info[1] if anime_info[1] else anime_info[0]
            if anime_info:
                anime_info_dict[anime_id] = {
                    'title_default': anime_info[0],
                    'title_english': anime_info[1],
                    'title_display': title_display,
                    'year': anime_info[2],
                    'episodes': anime_info[3],
                    'score': anime_info[4],
                    'image': anime_info[5],
                    'studio': anime_info[6]
                }

    return anime_info_dict

