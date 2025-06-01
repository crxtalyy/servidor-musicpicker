from flask import Flask, request, redirect, jsonify
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
import threading
import time
import random

app = Flask(__name__)

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="https://musicpicker-server.onrender.com/callback",
    scope="user-modify-playback-state user-read-playback-state"
)

token_info = None
ultimo_bpm = None
bpm_timestamp = None

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

        if bpm < 60:
            categoria = "relajado"
            estado = "Relajado"
        elif 60 <= bpm <= 120:
            categoria = "normal"
            estado = "Normal"
        else:
            categoria = "agitado"
            estado = "Agitado"

        uris = recomendar_canciones_por_estado(sp, categoria, bpm)
        if uris:
            sp.start_playback(uris=uris)
            print(f"▶️ [Manual] Reproduciendo lista para BPM {bpm} (categoría: {categoria})")
            return f"▶️ Reproduciendo {estado} para BPM {bpm}", 200
        else:
            return "❌ No se encontraron canciones recomendadas", 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def recomendar_canciones_por_estado(sp, categoria, bpm):
    # Parámetros según estado
    if categoria == "relajado":
        energy = 0.2
        valence = 0.4
        tempo = 70
    elif categoria == "normal":
        energy = 0.5
        valence = 0.6
        tempo = 100
    else:  # agitado
        energy = 0.8
        valence = 0.8
        tempo = 130

    try:
        recommendations = sp.recommendations(
            seed_genres=["pop", "rock", "indie", "chill", "latin"],
            limit=10,
            target_energy=energy,
            target_valence=valence,
            target_tempo=tempo
        )

        tracks = recommendations['tracks']
        if not tracks:
            print("⚠️ No se encontraron recomendaciones.")
            return None

        uris = [track['uri'] for track in tracks]
        print(f"🎧 Recomendadas {len(uris)} canciones para categoría {categoria}")
        return uris

    except Exception as e:
        print(f"❌ Error al obtener recomendaciones: {e}")
        return None

def reproductor_autonomo():
    global token_info, ultimo_bpm, bpm_timestamp
    while True:
        now = time.time()

        if token_info is None or ultimo_bpm is None or bpm_timestamp is None:
            time.sleep(2)
            continue

        # Si hace más de 15s que no llega un BPM nuevo, no reproducir
        if now - bpm_timestamp > 30:
            time.sleep(2)
            continue

        sp = get_spotify_client()
        if not sp:
            time.sleep(2)
            continue

        try:
            current = sp.current_playback()
            # Si no hay nada sonando, lanzar lista según último BPM
            if not current or not current["is_playing"]:
                bpm = ultimo_bpm
                if bpm < 60:
                    categoria = "relajado"
                elif 60 <= bpm <= 120:
                    categoria = "normal"
                else:
                    categoria = "agitado"

                uris = recomendar_canciones_por_estado(sp, categoria, bpm)
                if uris:
                    sp.start_playback(uris=uris)
                    print(f"▶️ [Autónomo] Reproduciendo lista para BPM {bpm} (categoría: {categoria})")
        except Exception as e:
            print(f"❌ Error en reproductor autónomo: {e}")

        time.sleep(5)

if __name__ == "__main__":
    hilo = threading.Thread(target=reproductor_autonomo, daemon=True)
    hilo.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
