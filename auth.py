import os
import time
from flask import session
from spotipy.oauth2 import SpotifyOAuth

# Configuración de autenticación con Spotify
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-modify-playback-state user-read-playback-state"
)

def get_token_info():
    token_info = session.get("token_info")
    if not token_info:
        return None

    now = int(time.time())
    expires_at = token_info.get('expires_at')
    refresh_token = token_info.get('refresh_token')

    # Validar que existan las claves necesarias
    if not expires_at or not refresh_token:
        return None

    if expires_at - now < 60:
        try:
            token_info = sp_oauth.refresh_access_token(refresh_token)
            session["token_info"] = token_info  # Actualizar en session
        except Exception as e:
            print("❌ Error al refrescar el token:", e)
            return None

    return token_info
