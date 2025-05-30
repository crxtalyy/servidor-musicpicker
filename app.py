from flask import Flask, request, redirect, jsonify
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
import random
import threading
import time

app = Flask(__name__)

# Autenticación Spotify
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="https://musicpicker-server.onrender.com/callback",
    scope="user-modify-playback-state user-read-playback-state"
)

token_info = None

# BPM más reciente y canciones reproducidas por estado
ultimo_bpm = None
reproducidas = {
    "relajado": [],
    "normal": [],
    "agitado": []
}

def get_spotify_client():
    global token_info
    if not token_info:
        return None
    return Spotify(auth=token_info["access_token"])

# Playlists por estado
canciones_relajado = [
    "spotify:track:44A0o4jA8F2ZF03Zacwlwx",
    "spotify:track:3aBGKDiAAvH2H7HLOyQ4US",
    "spotify:track:5JCoSi02qi3jJeHdZXMmR8"
]

canciones_normal = [
    "spotify:track:7EySX8ldJHoeWjJhJyZ8Tq",
    "spotify:track:465lkwZP4ZXzWqZq4kOhgW",
    "spotify:track:7e1arKsP7vPjdwssVPHgZk"
]

canciones_agitado = [
    "spotify:track:1j2iMeSWdsEP5ITCrZqbIL",
    "spotify:track:5Jh1i0no3vJ9u4deXkb4aV",
    "spotify:track:3SWGtKHaCFEUqfm9ydUFVw"
]

@app.route("/")
def home():
    return "🎵 Servidor Music Picker activo"

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    global token_info
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    return "✅ Autenticación completada"

@app.route("/play", methods=["POST"])
def play_music():
    global token_info, ultimo_bpm

    bpm = int(request.json.get("bpm", 0))
    ultimo_bpm = bpm  # Guardamos el último BPM recibido

    sp = get_spotify_client()
    if not sp:
        return "❌ Token inválido", 403

    try:
        current = sp.current_playback()

        # No cambiar la canción si ya hay una en reproducción
        if current and current["is_playing"]:
            return "🎵 Ya hay una canción reproduciéndose", 200

        # Elegir canción por BPM
        if bpm < 60:
            categoria = "relajado"
            estado = "Relajado"
        elif 60 <= bpm <= 120:
            categoria = "normal"
            estado = "Normal"
        else:
            categoria = "agitado"
            estado = "Agitado"

        uri = elegir_cancion(categoria)

        sp.start_playback(uris=[uri])
        return f"▶️ Reproduciendo {estado} para BPM {bpm}", 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cancion")
def cancion():
    global token_info
    if not token_info:
        return jsonify({"error": "Usuario no autenticado"}), 403

    spotify_uri = request.args.get("spotify_uri")
    if not spotify_uri:
        return jsonify({"error": "Falta parámetro spotify_uri"}), 400

    sp = get_spotify_client()
    try:
        track_id = spotify_uri.split(":")[-1]
        track = sp.track(track_id)
        return jsonify({
            "nombre": track['name'],
            "artista": track['artists'][0]['name']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def elegir_cancion(categoria):
    if categoria == "relajado":
        canciones = canciones_relajado
    elif categoria == "normal":
        canciones = canciones_normal
    else:
        canciones = canciones_agitado

    ya_reproducidas = reproducidas[categoria]
    disponibles = [c for c in canciones if c not in ya_reproducidas]

    if not disponibles:
        reproducidas[categoria] = []
        disponibles = canciones.copy()

    nueva = random.choice(disponibles)
    reproducidas[categoria].append(nueva)
    return nueva

def reproductor_autonomo():
    global token_info, ultimo_bpm
    while True:
        if token_info is None or ultimo_bpm is None:
            time.sleep(2)
            continue
        
        sp = get_spotify_client()
        if not sp:
            time.sleep(2)
            continue
        
        try:
            current = sp.current_playback()
            # Si no está reproduciendo nada y hay un BPM conocido, reproduce
            if not current or not current["is_playing"]:
                bpm = ultimo_bpm
                if bpm < 60:
                    categoria = "relajado"
                elif 60 <= bpm <= 120:
                    categoria = "normal"
                else:
                    categoria = "agitado"
                uri = elegir_cancion(categoria)
                sp.start_playback(uris=[uri])
                print(f"▶️ [Autónomo] Reproduciendo {categoria} para BPM {bpm}")
        except Exception as e:
            print(f"Error en reproductor autónomo: {e}")
        
        time.sleep(5)  # Espera 5 segundos antes de volver a chequear

if __name__ == "__main__":
    hilo = threading.Thread(target=reproductor_autonomo, daemon=True)
    hilo.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)