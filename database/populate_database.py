import sqlite3
import requests
import time
import numpy as np

conn = sqlite3.connect('animes.db')
cursor = conn.cursor()

def create_tables():

    # Creating Animes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Animes (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        english_name TEXT,
        year INTEGER,
        episodes INTEGER,
        score REAL,
        rank INTEGER,
        image TEXT
    )
    ''')

    # Creating Genres table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Genres (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
    ''')

    # Creating Themes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Themes (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
    ''')

    # Creating Studios table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Studios (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
    ''')

    # Creating Types table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    ''')

    # Creating Demographics table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Demographics (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
    ''')

    # Creating AnimeGenres junction table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS AnimeGenres (
        anime_id INTEGER NOT NULL,
        genre_id INTEGER NOT NULL,
        PRIMARY KEY (anime_id, genre_id),
        FOREIGN KEY (anime_id) REFERENCES Animes(id),
        FOREIGN KEY (genre_id) REFERENCES Genres(id)
    )
    ''')

    # Creating AnimeThemes junction table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS AnimeThemes (
        anime_id INTEGER NOT NULL,
        theme_id INTEGER NOT NULL,
        PRIMARY KEY (anime_id, theme_id),
        FOREIGN KEY (anime_id) REFERENCES Animes(id),
        FOREIGN KEY (theme_id) REFERENCES Themes(id)
    )
    ''')

    # Creating AnimeStudios junction table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS AnimeStudios (
        anime_id INTEGER NOT NULL,
        studio_id INTEGER NOT NULL,
        PRIMARY KEY (anime_id, studio_id),
        FOREIGN KEY (anime_id) REFERENCES Animes(id),
        FOREIGN KEY (studio_id) REFERENCES Studios(id)
    )
    ''')

    # Creating AnimeTypes junction table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS AnimeTypes (
        anime_id INTEGER NOT NULL,
        type_id INTEGER NOT NULL,
        PRIMARY KEY (anime_id, type_id),
        FOREIGN KEY (anime_id) REFERENCES Animes(id),
        FOREIGN KEY (type_id) REFERENCES Types(id)
    )
    ''')

    # Creating AnimeDemographics junction table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS AnimeDemographics (
        anime_id INTEGER NOT NULL,
        demographic_id INTEGER NOT NULL,
        PRIMARY KEY (anime_id, demographic_id),
        FOREIGN KEY (anime_id) REFERENCES Animes(id),
        FOREIGN KEY (demographic_id) REFERENCES Demographics(id)
    )
    ''')

    # Creating AnimeVectors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS AnimeVectors (
        anime_id INTEGER PRIMARY KEY,
        genre_vector TEXT,
        theme_vector TEXT,
        FOREIGN KEY (anime_id) REFERENCES Animes(id)
    )
    ''')

    conn.commit()
    print("Database and tables created successfully")

def add_anime(anime_id, name, english_name, year, episodes, score, rank, image):
    cursor.execute('''
    INSERT OR IGNORE INTO Animes (id, name, english_name, year, episodes, score, rank, image)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (anime_id, name, english_name, year, episodes, score, rank, image))


def add_genre(genre_id, name):
    cursor.execute('''
    INSERT OR IGNORE INTO Genres (id, name)
    VALUES (?, ?)
    ''', (genre_id, name))


def add_theme(theme_id, name):
    cursor.execute('''
    INSERT OR IGNORE INTO Themes (id, name)
    VALUES (?, ?)
    ''', (theme_id, name))


def add_studio(studio_id, name):
    cursor.execute('''
    INSERT OR IGNORE INTO Studios (id, name)
    VALUES (?, ?)
    ''', (studio_id, name))


def add_type(type_name):
    cursor.execute('''
    INSERT OR IGNORE INTO Types (name)
    VALUES (?)
    ''', (type_name,))
    cursor.execute('SELECT id FROM Types WHERE name = ?', (type_name,))

    result = cursor.fetchone()
    return result[0] if result else None


def add_demographics(demographics_id, name):
    cursor.execute('''
    INSERT OR IGNORE INTO Demographics (id, name)
    VALUES (?, ?)
    ''', (demographics_id, name))


def add_anime_genre(anime_id, genre_id):
    cursor.execute('''
    INSERT OR IGNORE INTO AnimeGenres (anime_id, genre_id)
    VALUES (?, ?)
    ''', (anime_id, genre_id))


def add_anime_theme(anime_id, theme_id):
    cursor.execute('''
    INSERT OR IGNORE INTO AnimeThemes (anime_id, theme_id)
    VALUES (?, ?)
    ''', (anime_id, theme_id))


def add_anime_studio(anime_id, studio_id):
    cursor.execute('''
    INSERT OR IGNORE INTO AnimeStudios (anime_id, studio_id)
    VALUES (?, ?)
    ''', (anime_id, studio_id))


def add_anime_type(anime_id, type_id):
    cursor.execute('''
    INSERT OR IGNORE INTO AnimeTypes (anime_id, type_id)
    VALUES (?, ?)
    ''', (anime_id, type_id))


def add_anime_demographic(anime_id, demographic_id):
    cursor.execute('''
    INSERT OR IGNORE INTO AnimeDemographics (anime_id, demographic_id)
    VALUES (?, ?)
    ''', (anime_id, demographic_id))

def build_anime_vectors():
    position = 0

    cursor.execute("SELECT id FROM Genres")
    all_genres = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT id FROM Themes")
    all_themes = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM Animes")
    all_anime_ids = [row[0] for row in cursor.fetchall()]
    
    for anime_id in all_anime_ids:
        genre_vector = np.zeros(len(all_genres))
        theme_vector = np.zeros(len(all_themes))
        
        # Fetch genres for this anime
        cursor.execute("""
            SELECT genre_id
            FROM AnimeGenres
            WHERE anime_id = ?
        """, (anime_id,))
        genres = cursor.fetchall()
        
        for genre_id in genres:
            genre_vector[all_genres.index(genre_id[0])] = 1
        
        # Fetch themes for this anime
        cursor.execute("""
            SELECT theme_id
            FROM AnimeThemes
            WHERE anime_id = ?
        """, (anime_id,))
        themes = cursor.fetchall()
        
        for theme_id in themes:
            theme_vector[all_themes.index(theme_id[0])] = 1
        
        genre_vector_str = ",".join(map(str, genre_vector.astype(int)))
        theme_vector_str = ",".join(map(str, theme_vector.astype(int)))
        
        cursor.execute("""
            INSERT OR REPLACE INTO AnimeVectors (anime_id, genre_vector, theme_vector)
            VALUES (?, ?, ?)
        """, (anime_id, genre_vector_str, theme_vector_str))

        
        position += 1
        print(f"Progress: {position}/{len(all_anime_ids)}", end='\r')

    conn.commit()
    cursor.close()
    conn.close()


def fetch_anime_data(page):
    url = f'https://api.jikan.moe/v4/anime?page={page}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        total_items = data['pagination']['items']['total']
        current_page_count = len(data['data'])

        count_analyzed = (page - 1) * 25 + current_page_count
        
        print(f"Data analyzed: {count_analyzed} of {total_items} | Page: {page}", end='\r')
        
        return data['data']
    else:
        print(f"Failed to fetch data: {response.status_code}")
        print(f"Page: {page}")
        return []


def populate_tables():
    page = 1
    while True:
        anime_data = fetch_anime_data(page)
        if not anime_data:
            conn.commit()
            break
        
        for anime in anime_data:
            anime_id = anime['mal_id']
            name = anime['title']
            english_name = anime['title_english']
            year = anime['year']
            episodes = anime['episodes']
            score = anime['score']
            rank = anime['rank']
            image = anime['images']['jpg']['image_url']
            
            add_anime(anime_id, name, english_name, year, episodes, score, rank, image)

            anime_type = anime['type']
            type_id = add_type(anime_type)
            add_anime_type(anime_id, type_id)

            genres = anime.get('genres', [])
            for genre in genres:
                genre_id = genre['mal_id']
                genre_name = genre['name']
                add_genre(genre_id, genre_name)
                add_anime_genre(anime_id, genre_id)
                
            themes = anime.get('themes', [])
            for theme in themes:
                theme_id = theme['mal_id']
                theme_name = theme['name']
                add_theme(theme_id, theme_name)
                add_anime_theme(anime_id, theme_id)
            
            studios = anime.get('studios', [])
            for studio in studios:
                studio_id = studio['mal_id']
                studio_name = studio['name']
                add_studio(studio_id, studio_name)
                add_anime_studio(anime_id, studio_id)

            demographics = anime.get('demographics', [])
            for demographic in demographics:
                demographic_id = demographic['mal_id']
                demographic_name = demographic['name']
                add_demographics(demographic_id, demographic_name)
                add_anime_demographic(anime_id, demographic_id)


        conn.commit()
        time.sleep(1)  # The API does not allow more than 60 requests per minute.
        page += 1

    print()
    print("==========================")
    print("Data population completed!")
    print("==========================")

print("Creating database with tables...")
create_tables()

print("Populating tables...")
populate_tables()

print("Building anime vectors...")
build_anime_vectors()

print()
print("Done!")