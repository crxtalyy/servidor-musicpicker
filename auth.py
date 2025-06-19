import os
import time
from spotipy.oauth2 import SpotifyOAuth

# Autenticación para TU cuenta
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-modify-playback-state user-read-playback-state"
)

_token_info = None  # Guardamos el token globalmente

def set_token_info(token):
    global _token_info
    _token_info = token

def get_token_info():
    global _token_info
    if not _token_info:
        return None

    now = int(time.time())
    if _token_info.get('expires_at', 0) - now < 60:
        try:
            _token_info = sp_oauth.refresh_access_token(_token_info['refresh_token'])
        except Exception as e:
            print("❌ Error al refrescar token:", e)
            return None

    return _token_info
