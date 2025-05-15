from flask import Flask, request, redirect
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
import random

app = Flask(__name__)

# Configuración de Spotify OAuth
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="https://musicpicker-server.onrender.com/callback",  # ⚠️ Este es tu URL real con /callback
    scope="user-modify-playback-state"
)


# Guardar token para la sesión
token_info = None

# Canciones por estado emocional
canciones_relajado = [
    "spotify:track:5nNmj1cLH3r4aA4XDJ2bgY",  # Je te laisserai des mots - Patrick Watson
    "spotify:track:4kkl6Wt7JHhVAzWbvzCcE6",  # Glimpse of Us - Joji
    "spotify:track:5wANPM4fQCJwkGd4rN57mH",  # favorite crime - Olivia Rodrigo
]

canciones_normal = [
    "spotify:track:1FoKhG7HP9AJm7nBxz6hX5",  # Si tú me quisieras - Mon Laferte
    "spotify:track:4QGW5KkT3URwd38QVc99gl",  # La Verdad - Kidd Voodoo
    "spotify:track:4UoYkF2wnc5n4jqbH5azvB",  # poison poison - Reneé Rapp
]

canciones_agitado = [
    "spotify:track:0VgkVdmE4gld66l8iyGjgx",  # Be Someone - Benson Boone
    "spotify:track:2dHHgzDwk4BJdRwy9uXhTO",  # So American - Olivia Rodrigo
    "spotify:track:6DXk1aLxSk2K2fJUSFbP6G",  # Disaster - Conan Gray
]



@app.route("/cancion")
def cancion():
    global token_info
    if not token_info:
        return jsonify({"error": "Usuario no autenticado. Visita /login primero."}), 403
    
    spotify_uri = request.args.get("spotify_uri")
    if not spotify_uri:
        return jsonify({"error": "Falta el parámetro spotify_uri"}), 400
    
    sp = get_spotify_client()
    if sp is None:
        return jsonify({"error": "Token no válido"}), 403
    
    try:
        track_id = spotify_uri.split(":")[-1]  # extraer id si es URI completo
        track = sp.track(track_id)
        nombre = track['name']
        artista = track['artists'][0]['name']
        return jsonify({"nombre": nombre, "artista": artista})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

    # Elegir una canción aleatoria según BPM
    if bpm < 60:
        uri = random.choice(canciones_relajado)
        estado = "Relajado"
    elif 60 <= bpm <= 120:
        uri = random.choice(canciones_normal)
        estado = "Normal"
    else:
        uri = random.choice(canciones_agitado)
        estado = "Agitado"

    sp.start_playback(uris=[uri])
    return f"Reproduciendo canción del estado {estado} para BPM {bpm}."

# Permite que Render use el puerto asignado
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
