import os
import uuid
import time
from flask import redirect, request, session
from spotipy.oauth2 import SpotifyOAuth

ultimo_token = None

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-read-playback-state user-modify-playback-state"
)

def login():
    session["user_id"] = str(uuid.uuid4())
    return redirect(sp_oauth.get_authorize_url())

def callback():
    global ultimo_token
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    ultimo_token = token_info
    print(f"➡️ Callback ejecutado, token asignado: {token_info}")
    return redirect("/dashboard")

def get_valid_token():
    global ultimo_token
    if ultimo_token:
        now = int(time.time())
        # refrescar si expira en menos de 60 segundos
        if ultimo_token['expires_at'] - now < 60:
            token_info = sp_oauth.refresh_access_token(ultimo_token['refresh_token'])
            ultimo_token = token_info
    return ultimo_token