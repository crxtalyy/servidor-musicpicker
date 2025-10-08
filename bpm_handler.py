from flask import Blueprint, request, jsonify
from spotipy import Spotify
from auth import get_token_info
import random

bpm_blueprint = Blueprint("bpm", __name__)

playlist_uris = {
    "relajado": "spotify:playlist:2ObbFHzjAw5yucJ57MbqOn",
    "normal":   "spotify:playlist:3Lqw8YaDSWQRTkiIejggVT",
    "agitado":  "spotify:playlist:37i9dQZF1EIgSjgoYBB2M6"
}

# Endpoint para recibir BPM y reproducir canción
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

        # Comprobar si ya hay música reproduciéndose
        current = sp.current_playback()
        if current and current.get("is_playing"):
            track_name = current["item"]["name"]
            return jsonify({"message": "BPM recibido", "cancion": track_name, "ya_reproduciendo": True}), 200

        # No hay música reproduciéndose → seleccionar canción aleatoria
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
        track_name = track["name"]

        return jsonify({"message": "BPM recibido", "cancion": track_name, "ya_reproduciendo": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para consultar si hay música reproduciéndose
@bpm_blueprint.route("/estado_musica", methods=["GET"])
def estado_musica():
    try:
        token_info = get_token_info()
        if not token_info:
            return jsonify({"error": "Token inválido"}), 403

        sp = Spotify(auth=token_info["access_token"])
        current = sp.current_playback()
        if current and current.get("is_playing"):
            cancion = current["item"]["name"]
            return jsonify({"reproduciendo": True, "cancion": cancion}), 200
        else:
            return jsonify({"reproduciendo": False, "cancion": None}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500