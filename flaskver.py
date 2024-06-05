import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, session, redirect, request, url_for
from spotipy.cache_handler import FlaskSessionCacheHandler
from sqlsample import get_connection
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

# Spotify authentication route
@app.route('/')
def home():
    token_info = cache_handler.get_cached_token()
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    
    # Initialize the Spotify client with the valid access token
    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.current_user_saved_tracks()
    tracks_info = ""
    for idx, item in enumerate(results['items']):
        track = item['track']
        tracks_info += f"{idx+1}: {track['artists'][0]['name']} - {track['name']}<br>"
    return redirect(url_for('pulltopartists'))

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
