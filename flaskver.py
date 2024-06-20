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
            CREATE TABLE IF NOT EXISTS user_top_songs (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255)
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
    with connection.cursor() as cursor:
        for track in top_tracks['items']:
            cursor.execute("""
                INSERT INTO user_top_songs (id, name) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE name = VALUES(name);
            """, (track['id'], track['name']))
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
    return redirect(url_for('potential_recommendations'))

@app.route('/user_top_songs')
def user_top_songs():
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM user_top_songs;")
        user_top_songs = cursor.fetchall()
    return render_template(r"table.html", title='User Top Songs', items=user_top_songs)

@app.route('/potential-recommendations')
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
    app.run(debug=True)
