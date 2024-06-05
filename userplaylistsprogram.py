import spotipy
from spotipy.oauth2 import SpotifyOAuth

scope = "user-library-read"
client_id = "f43830319e8943f2994558f9c8a5f72b"  # Replace with your actual Spotify client ID
redirect_uri = "http://localhost:5000/callback"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=client_id, redirect_uri=redirect_uri))

results = sp.current_user_saved_tracks()
for idx, item in enumerate(results['items']):
    track = item['track']
    print(idx, track['artists'][0]['name'], " – ", track['name'])

