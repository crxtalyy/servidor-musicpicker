import time
import random
from flask import Blueprint, request, jsonify
from spotipy import Spotify
from auth import get_token_info

bpm_blueprint = Blueprint("bpm", __name__)

playlist_uris = {
    "relajado": "spotify:playlist:2ObbFHzjAw5yucJ57MbqOn",
    "normal":   "spotify:playlist:5HbYdtp5UcWgQoL4RIn4Nz",
    "agitado":  "spotify:playlist:37i9dQZF1EIgSjgoYBB2M6"
}

# --- Endpoint para recibir BPM desde la Raspberry ---
@bpm_blueprint.route("/bpm", methods=["POST"])
def recibir_bpm():
    data = request.get_json()
    if not data or "bpm" not in data:
        return jsonify({"error": "Se requiere el valor 'bpm'"}), 400

    try:
        bpm = int(data["bpm"])
        if bpm < 75:
            categoria = "relajado"
        elif bpm <= 110:
            categoria = "normal"
        else:
            categoria = "agitado"

        token_info = get_token_info()
        if not token_info:
            return jsonify({"error": "Token inválido"}), 403

        sp = Spotify(auth=token_info["access_token"])
        playlist_uri = playlist_uris[categoria]

        # --- Verificar si hay música reproduciéndose ---
        playback = sp.current_playback()
        if playback and playback.get("is_playing"):
            current_track = playback["item"]["name"] if playback["item"] else "Desconocida"
            print(f"🎵 Música ya en reproducción: {current_track}")
            return jsonify({"message": "BPM recibido", "cancion": current_track, "ya_reproduciendo": True}), 200

        # --- Elegir canción aleatoria si NO hay música ---
        playlist = sp.playlist(playlist_uri)
        tracks = playlist["tracks"]["items"]
        total_tracks = len(tracks)
        if total_tracks == 0:
            return jsonify({"error": "Playlist vacía"}), 500

        random_index = random.randint(0, total_tracks - 1)
        track = tracks[random_index]["track"]
        track_uri = track["uri"]

        sp.start_playback(uris=[track_uri])
        song_name = track["name"]

        print(f"▶️ BPM {bpm} → Estado: {categoria} → Canción: {song_name}")
        return jsonify({"message": "BPM recibido", "cancion": song_name, "ya_reproduciendo": False}), 200

    except Exception as e:
        print(f"❌ Error en /bpm: {e}")
        return jsonify({"error": str(e)}), 500