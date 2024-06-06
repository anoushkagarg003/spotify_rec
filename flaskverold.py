import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, session, redirect, request, url_for, render_template
from spotipy.cache_handler import FlaskSessionCacheHandler
from sqlsample import get_connection, execute_query
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

def create_tables():
    with connection.cursor() as cursor:
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS potential_recommendations (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255)
            );
        """)
    connection.commit()

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
    for artist_id in artists.keys():
        similar_artists = sp.artist_related_artists(artist_id)
    
        with connection.cursor() as cursor:
            for artist in similar_artists['artists']:
                similar_artist_id = artist['id']
            similar_artist_name = artist['name']
            
            # Fetch top tracks of each similar artist
            top_tracks = sp.artist_top_tracks(similar_artist_id)
            for track in top_tracks['tracks']:
                cursor.execute("""
                    INSERT INTO potential_recommendations (id, name) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE name = VALUES(name);
                """, (track['id'], track['name']))
    connection.commit()
    return redirect(url_for('user_top_songs'))

@app.route('/user_top_songs')
def user_top_songs():
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM user_top_songs_1;")
        user_top_songs = cursor.fetchall()
        print(user_top_songs)
    return render_template(r"table.html", title='User Top Songs', items=user_top_songs)

@app.route('/potential_recommendations')
def potential_recommendations():
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM potential_recommendations;")
        potential_recommendations = cursor.fetchall()
    return render_template('table.html', title='Potential Recommendations', items=potential_recommendations)

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
