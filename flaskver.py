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
    return redirect(url_for('user_top_songs'))

@app.route('/user_top_songs')
def user_top_songs():
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM user_top_songs;")
        user_top_songs = cursor.fetchall()
    return render_template(r"table.html", title='User Top Songs', items=user_top_songs)

@app.route('/me/top/tracks/')
def pulltoptrack():
    token_info = cache_handler.get_cached_token()
    if not token_info:
        redirect(url_for('home'))
    sp = spotipy.Spotify(auth=token_info['access_token'])
    top_tracks=sp.current_user_top_tracks(limit=50, offset=0, time_range='medium_term')
    tracks={}
    for i,x in enumerate(top_tracks['items']):
        tracks[x['id']]=x['name']

@app.route('/me/top/artists/')
def pulltopartists():
    token_info = cache_handler.get_cached_token()
    if not token_info:
        redirect(url_for('home'))
    sp = spotipy.Spotify(auth=token_info['access_token'])
    top_artists=sp.current_user_top_artists(limit=50, offset=0, time_range='medium_term')
    artists={}
    artists_str=""
    for i,x in enumerate(top_artists['items']):
        artists[x['id']]=x['name']
        artists_str+= f"{x['id']}: {x['name']}<br>"
    return redirect(url_for('similar_artists', id=next(iter(artists))))
    
@app.route('/artists/<id>/related-artists/')
def similar_artists(id):
    token_info = cache_handler.get_cached_token()
    if not token_info:
        redirect(url_for('home'))
    sp = spotipy.Spotify(auth=token_info['access_token'])
    similar_artists=sp.artist_related_artists(id)
    s_art={}
    s_str=''
    for x in similar_artists['artists']:
        s_art[x['id']]= x['name']
        s_str+= f"{x['id']} : {x['name']}<br>"
    return redirect(url_for('toptracks', id=next(iter(s_art))))

@app.route("/artists/<id>/top-tracks/")
def toptracks(id):
    token_info = cache_handler.get_cached_token()
    if not token_info:
        redirect(url_for('home'))
    sp = spotipy.Spotify(auth=token_info['access_token'])
    tracks=sp.artist_top_tracks(id)
    track_dict={}
    t_str=''
    for x in tracks['tracks']:
        track_dict[x['id']]= x['name']
        t_str+=f"{x['id']} : {x['name']}<br>"
    return t_str

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
