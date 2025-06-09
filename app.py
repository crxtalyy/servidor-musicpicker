from flask import Flask, request, redirect, jsonify
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
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
ultimo_bpm = None
bpm_timestamp = None
estado_actual = None  # Guarda el estado emocional actual

# ✅ NUEVAS playlists según estado
playlist_uris = {
    "relajado": "spotify:playlist:2ObbFHzjAw5yucJ57MbqOn",
    "normal":   "spotify:playlist:37i9dQZF1DWSoyxGghlqv5",
    "agitado":  "spotify:playlist:37i9dQZF1EIgSjgoYBB2M6"
}

def get_spotify_client():
    global token_info
    if not token_info:
        return None
    return Spotify(auth=token_info["access_token"])

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
    global token_info, ultimo_bpm, bpm_timestamp

    bpm = int(request.json.get("bpm", 0))
    ultimo_bpm = bpm
    bpm_timestamp = time.time()

    sp = get_spotify_client()
    if not sp:
        return "❌ Token inválido", 403

    try:
        current = sp.current_playback()

        if current and current["is_playing"]:
            return "🎵 Ya hay una canción reproduciéndose", 200

        if bpm < 75:
            categoria = "relajado"
        elif 75 <= bpm <= 110:
            categoria = "normal"
        else:
            categoria = "agitado"

        playlist_uri = playlist_uris[categoria]
        sp.start_playback(context_uri=playlist_uri)
        print(f"▶️ [Manual] Reproduciendo playlist para BPM {bpm} (estado: {categoria})")

        return f"▶️ Reproduciendo playlist de estado {categoria} para BPM {bpm}", 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def reproductor_autonomo():
    global token_info, ultimo_bpm, bpm_timestamp, estado_actual
    while True:
        now = time.time()

        if token_info is None or ultimo_bpm is None or bpm_timestamp is None:
            time.sleep(2)
            continue

        # Espera activa si no hay nuevo BPM en los últimos 10 segundos
        if now - bpm_timestamp > 10:
            time.sleep(2)
            continue

        sp = get_spotify_client()
        if not sp:
            time.sleep(2)
            continue

        try:
            current = sp.current_playback()
            if not current:
                time.sleep(2)
                continue

            bpm = ultimo_bpm
            if bpm < 75:
                nuevo_estado = "relajado"
            elif 75 <= bpm <= 110:
                nuevo_estado = "normal"
            else:
                nuevo_estado = "agitado"

            # Cambio de estado: se reproduce nueva playlist
            if nuevo_estado != estado_actual:
                if not current["is_playing"] or current["progress_ms"] >= current["item"]["duration_ms"] - 1000:
                    playlist_uri = playlist_uris[nuevo_estado]
                    sp.start_playback(context_uri=playlist_uri)
                    estado_actual = nuevo_estado
                    print(f"▶️ [Cambio de estado] Reproduciendo nueva playlist ({nuevo_estado}): {playlist_uri}")

        except Exception as e:
            print(f"❌ Error en reproductor autónomo: {e}")

        time.sleep(5)

if __name__ == "__main__":
    hilo = threading.Thread(target=reproductor_autonomo, daemon=True)
    hilo.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
