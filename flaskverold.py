import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, session, redirect, request, render_template, url_for
from spotipy.cache_handler import FlaskSessionCacheHandler
from sqlsample import get_connection
import time
import subprocess
from pymysql.err import OperationalError
import pandas as pd
from datetime import datetime
connection=get_connection()

scope = "user-library-read, user-top-read"
client_id = "f43830319e8943f2994558f9c8a5f72b"  # Replace with your actual Spotify client ID
client_secret = "dff5190ed19c4fb7af09d8d83de09a6b"  # Replace with your actual Spotify client secret
redirect_uri = "http://localhost:5000/callback"

# Configure Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secret key for session management

# Configure SpotifyOAuth and FlaskSessionCacheHandler
cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(scope=scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, cache_handler=cache_handler, show_dialog=True)
def standardize_date(date_str):
    date_formats = [
    '%Y-%m-%d',  # Year, month, day
    '%Y-%m',     # Year, month
    '%Y'         # Year only
    ]
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            if fmt == '%Y':
                date_obj = date_obj.replace(month=1, day=1)
            elif fmt == '%Y-%m':
                date_obj = date_obj.replace(day=1)
            return date_obj
        except ValueError:
            continue
    return None

def create_tables():
    try:
        with connection.cursor() as cursor:
            # Drop and create user_top_songs_1 table
            cursor.execute("DROP TABLE IF EXISTS user_top_songs_1;")
            
            # Committing the drop operation
            connection.commit()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_top_songs_1 (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255),
                    acousticness FLOAT,
                    danceability FLOAT,
                    duration_ms INT,
                    energy FLOAT,
                    instrumentalness FLOAT,
                    `key` INT,
                    liveness FLOAT,
                    loudness FLOAT,
                    mode INT,
                    speechiness FLOAT,
                    tempo FLOAT,
                    time_signature INT,
                    valence FLOAT
                );
            """)
            
            # Sleep for 10 seconds (if this is necessary)
            time.sleep(10)
            cursor.execute("DROP TABLE IF EXISTS potential_recommendations_2;")
            
            # Committing the drop operation
            connection.commit()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS potential_recommendations_2 (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255),
                    acousticness FLOAT,
                    danceability FLOAT,
                    duration_ms INT,
                    energy FLOAT,
                    instrumentalness FLOAT,
                    key_value INT,
                    liveness FLOAT,
                    loudness FLOAT,
                    mode INT,
                    speechiness FLOAT,
                    tempo FLOAT,
                    time_signature INT,
                    valence FLOAT,
                    release_date DATE
                );
            """)
        
        connection.commit()  # Committing changes to the database
    
    except OperationalError as e:
        print(f"The error '{e}' occurred")
        connection.rollback()  # Rolling back changes in case of error

# Spotify authentication route
@app.route('/')
def home():
    token_info = cache_handler.get_cached_token()
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    sp = spotipy.Spotify(auth=token_info['access_token'])
    top_tracks = sp.current_user_top_tracks(limit=50, offset=0, time_range='medium_term')
    track_ids = [track['id'] for track in top_tracks['items']]
    # Fetch audio features for top tracks
    audio_features = sp.audio_features(tracks=track_ids)
    with connection.cursor() as cursor:
        for track, features in zip(top_tracks['items'], audio_features):
            cursor.execute("""
            INSERT INTO user_top_songs_1 (id, name, acousticness, danceability, duration_ms, energy, instrumentalness, `key`, liveness, loudness, mode, speechiness, tempo, time_signature, valence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                acousticness = VALUES(acousticness),
                danceability = VALUES(danceability),
                duration_ms = VALUES(duration_ms),
                energy = VALUES(energy),
                instrumentalness = VALUES(instrumentalness),
                `key` = VALUES(`key`),
                liveness = VALUES(liveness),
                loudness = VALUES(loudness),
                mode = VALUES(mode),
                speechiness = VALUES(speechiness),
                tempo = VALUES(tempo),
                time_signature = VALUES(time_signature),
                valence = VALUES(valence);
        """, (
            track['id'], 
            track['name'], 
            features['acousticness'], 
            features['danceability'], 
            features['duration_ms'], 
            features['energy'], 
            features['instrumentalness'], 
            features['key'], 
            features['liveness'], 
            features['loudness'], 
            features['mode'], 
            features['speechiness'], 
            features['tempo'], 
            features['time_signature'], 
            features['valence']
        ))
    connection.commit()
    top_artists = sp.current_user_top_artists(limit=50, offset=0, time_range='medium_term')
    artists = {artist['id']: artist['name'] for artist in top_artists['items']}

    # Process each top artist to find similar artists and their top tracks
    track_ids=[]
    for artist_id in artists.keys():
        '''similar_artists = sp.artist_related_artists(artist_id)
        for artist in similar_artists['artists']:
            similar_artist_id = artist['id']
            # Fetch top tracks of each similar artist'''
        top_tracks = sp.artist_top_tracks(artist_id)
                # Prepare a list of track IDs for audio features retrieval
        for track in top_tracks['tracks']:
            track_ids.append(track['id'])
    new_releases=sp.new_releases(limit=20)
    track_dict={}
    album_ids = [album['id'] for album in new_releases['albums']['items']]
    album_dict = {album['id']: album['release_date'] for album in new_releases['albums']['items']}
    for album_id in album_dict:
        album_dict[album_id] = standardize_date(album_dict[album_id]) 
    print(album_dict)
    for album_id in album_ids:
        recent_tracks=sp.album_tracks(album_id=album_id,limit=20)
        for track in recent_tracks['items']:
            track_id = track['id']
            release_date = album_dict.get(album_id)  # Get the release date from album_dict
        # If release_date is None, skip adding to track_dict
            if release_date:
                track_dict[track_id] = release_date
        track_ids.extend([track['id'] for track in recent_tracks['items']])
        
    for i in range(0, len(track_ids), 100):
        chunk = track_ids[i:i + 100]
        audio_features1 = sp.audio_features(tracks=chunk)
        audio_features.extend(audio_features1)
                # Insert potential recommendations into the database
                #for track, track_info in zip(audio_features, track_ids_names):
                #time.sleep(10)
    with connection.cursor() as cursor:
            for track in audio_features:
                release_date=track_dict.get(track['id'],None)
                cursor.execute("""
                            INSERT INTO potential_recommendations_2 
                            (id, name, acousticness, danceability, duration_ms, energy, 
                             instrumentalness, key_value, liveness, loudness, mode, 
                             speechiness, tempo, time_signature, valence, release_date) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                            name = VALUES(name), 
                            acousticness = VALUES(acousticness), 
                            danceability = VALUES(danceability), 
                            duration_ms = VALUES(duration_ms), 
                            energy = VALUES(energy), 
                            instrumentalness = VALUES(instrumentalness), 
                            key_value = VALUES(key_value), 
                            liveness = VALUES(liveness), 
                            loudness = VALUES(loudness), 
                            mode = VALUES(mode), 
                            speechiness = VALUES(speechiness), 
                            tempo = VALUES(tempo), 
                            time_signature = VALUES(time_signature), 
                            valence = VALUES(valence),
                            release_date = VALUES(release_date);
                        """, (track['id'], None , track['acousticness'], 
                              track['danceability'], track['duration_ms'], track['energy'], 
                              track['instrumentalness'], track['key'], track['liveness'], 
                              track['loudness'], track['mode'], track['speechiness'], 
                              track['tempo'], track['time_signature'], track['valence'], release_date))
    connection.commit()
    from recsystemredone import get_recommendations
    top_10_ids=get_recommendations()
    print(top_10_ids)
    info=sp.tracks(top_10_ids)
    print(info)
    i=0
    df_recs = pd.DataFrame(columns=['id', 'preview_url', 'play_link','name'])
    rows = []

    for id, x in zip(top_10_ids, info['tracks']):
        url = x['external_urls']['spotify']  # Extract Spotify URL
        preview_url = x['preview_url']
        name = x['name']
        rows.append({'id': id, 'preview_url': preview_url, 'play_link': url, 'name': name})
    df_recs = pd.DataFrame(rows)
    session['df_recs'] = df_recs.to_json(orient='split')
    return redirect(url_for('potential_recommendations'))


@app.route('/user_top_songs')
def user_top_songs():
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM user_top_songs_1;")
        user_top_songs = cursor.fetchall()
        cursor.execute("SELECT * FROM potential_recommendations_2;")
        potential_recommendations = cursor.fetchall()
        print(user_top_songs)
    return 'none'

@app.route('/potential_recommendations')
def potential_recommendations():
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM potential_recommendations_2;")
        potential_recommendations = cursor.fetchall()
    from recsystemredone import get_recommendations
    df_recs_json = session.get('df_recs')
    if df_recs_json:
        df_recs = pd.read_json(df_recs_json, orient='split')
        return df_recs.to_html() 
    return 'none'

# Callback route
@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    # Store the token info in session for further requests
    session['token_info'] = token_info
    return redirect('/')

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
