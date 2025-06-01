from flask import Flask, request, redirect, jsonify
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
import threading
import time

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
        print("❌ No hay token aún")
        return None

    if sp_oauth.is_token_expired(token_info):
        print("🔄 Refrescando token Spotify...")
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
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
    print("✅ Autenticación completada")
    return "✅ Autenticación completada"

@app.route("/play", methods=["POST"])
def play_music():
    global token_info, ultimo_bpm, bpm_timestamp

    bpm = request.json.get("bpm")
    if bpm is None:
        return "❌ No se envió BPM", 400

    try:
        bpm = float(bpm)
    except:
        return "❌ BPM inválido", 400

    ultimo_bpm = bpm
    bpm_timestamp = time.time()
    print(f"💓 BPM detectado: {bpm}")

    sp = get_spotify_client()
    if not sp:
        return "❌ Token inválido o no autenticado", 403

    try:
        current = sp.current_playback()
        if current and current["is_playing"]:
            print("🎵 Ya hay música sonando, no se inicia otra lista")
            return "🎵 Música ya sonando", 200

        if bpm < 60:
            categoria = "relajado"
        elif 60 <= bpm <= 120:
            categoria = "normal"
        else:
            categoria = "agitado"

        uris = recomendar_canciones_por_estado(sp, categoria, bpm)
        if uris:
            sp.start_playback(uris=uris)
            print(f"▶️ [Manual] Reproduciendo lista para BPM {bpm} (categoría: {categoria})")
            return f"▶️ Reproduciendo lista {categoria} para BPM {bpm}", 200
        else:
            print("❌ No se encontraron canciones recomendadas")
            return "❌ No se encontraron canciones recomendadas", 500

    except Exception as e:
        print(f"❌ Error en play_music: {e}")
        return jsonify({"error": str(e)}), 500

def recomendar_canciones_por_estado(sp, categoria, bpm):
    # Parámestros relajados para no ser muy restrictivos
    if categoria == "relajado":
        target_energy = 0.3
        target_valence = 0.3
        target_tempo = 60
    elif categoria == "normal":
        target_energy = 0.5
        target_valence = 0.5
        target_tempo = 90
    else:  # agitado
        target_energy = 0.7
        target_valence = 0.7
        target_tempo = 120

    print(f"🎧 Pidiendo recomendaciones para '{categoria}' con energy={target_energy}, valence={target_valence}, tempo={target_tempo}")

    try:
        recommendations = sp.recommendations(
            seed_genres=["pop", "rock", "indie"],
            limit=10,
            target_energy=target_energy,
            target_valence=target_valence,
            target_tempo=target_tempo
        )
        print("Respuesta de recomendaciones:", recommendations)

        tracks = recommendations.get('tracks', [])
        if not tracks:
            print("⚠️ No se encontraron canciones recomendadas en Spotify")
            return None

        uris = [track['uri'] for track in tracks]
        print(f"🎶 Se encontraron {len(uris)} canciones")
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

        # Si hace más de 45 segundos que no llega BPM nuevo, no reproducir
        if now - bpm_timestamp > 45:
            time.sleep(2)
            continue

        sp = get_spotify_client()
        if not sp:
            time.sleep(2)
            continue

        try:
            current = sp.current_playback()
            # Si no hay reproducción activa, lanzar lista según último BPM
            if not current or not current.get("is_playing", False):
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
