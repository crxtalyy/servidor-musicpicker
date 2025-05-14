from flask import Flask, request, redirect
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os

app = Flask(__name__)

# Configuración de Spotify OAuth
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),  # usa variable de entorno
    scope="user-modify-playback-state"
)

# Guardar token para la sesión
token_info = None

@app.route("/")
def home():
    return "Servidor Music Picker funcionando 🎵"

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    global token_info
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    return "¡Autenticación completa! Ya puedes enviar BPM."

@app.route("/play", methods=["POST"])
def play_music():
    global token_info
    bpm = int(request.json.get("bpm", 0))
    
    if not token_info:
        return "Usuario no autenticado. Visita /login primero.", 403
    
    sp = Spotify(auth=token_info["access_token"])

    # Elegir canción según BPM
    if bpm < 60:
        uri = "spotify:track:3KkXRkHbMCARz0aVfEt68P"  # relajado
    elif 60 <= bpm <= 120:
        uri = "spotify:track:6habFhsOp2NvshLv26DqMb"  # normal
    else:
        uri = "spotify:track:2bgTy3xyD0A7XzRtEMxO0P"  # agitado

    sp.start_playback(uris=[uri])
    return f"Reproduciendo canción para BPM {bpm}"

# Este bloque permite que Render escuche en el puerto asignado externamente
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)