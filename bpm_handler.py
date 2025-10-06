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

# --- Variables globales para controlar reproducción ---
cancion_actual = None
reproduciendo = False
categoria_actual = None

# --- Endpoint para recibir BPM desde la Raspberry ---
@bpm_blueprint.route("/bpm", methods=["POST"])
def recibir_bpm():
    global cancion_actual, reproduciendo, categoria_actual

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
        
        # Verificar si ya hay música reproduciéndose
        if reproduciendo and categoria == categoria_actual:
            # No cambiamos la canción, devolvemos la actual
            print(f"🎵 BPM {bpm} → Estado: {categoria} → Canción actual sigue: {cancion_actual}")
            return jsonify({
                "message": "BPM recibido",
                "cancion": cancion_actual,
                "ya_reproduciendo": True
            }), 200

        # Si no hay música o cambió la categoría, reproducir nueva canción
        playlist_uri = playlist_uris[categoria]
        playlist = sp.playlist(playlist_uri)
        tracks = playlist["tracks"]["items"]
        total_tracks = len(tracks)
        if total_tracks == 0:
            return jsonify({"error": "Playlist vacía"}), 500

        random_index = random.randint(0, total_tracks - 1)
        track = tracks[random_index]["track"]
        track_uri = track["uri"]

        sp.start_playback(uris=[track_uri])
        cancion_actual = track["name"]
        categoria_actual = categoria
        reproduciendo = True

        print(f"▶️ BPM {bpm} → Estado: {categoria} → Nueva canción: {cancion_actual}")
        return jsonify({
            "message": "BPM recibido",
            "cancion": cancion_actual,
            "ya_reproduciendo": True
        }), 200

    except Exception as e:
        print(f"❌ Error en /bpm: {e}")
        # Si falla la reproducción, marcamos que no hay música
        reproduciendo = False
        cancion_actual = None
        categoria_actual = None
        return jsonify({"error": str(e)}), 500