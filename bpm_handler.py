from flask import request, jsonify
from spotipy import Spotify
from auth import ultimo_token

playlist_uris = {
    "relajado": "spotify:playlist:2ObbFHzjAw5yucJ57MbqOn",
    "normal":   "spotify:playlist:37i9dQZF1DWSoyxGghlqv5",
    "agitado":  "spotify:playlist:37i9dQZF1EIgSjgoYBB2M6"
}

def recibir_bpm():
    data = request.json or {}
    bpm = int(data.get("bpm", 0))

    if not ultimo_token:
        return "❌ No hay usuario autenticado", 401

    sp = Spotify(auth=ultimo_token["access_token"])

    if bpm < 75:
        estado = "relajado"
    elif bpm <= 110:
        estado = "normal"
    else:
        estado = "agitado"

    try:
        sp.start_playback(context_uri=playlist_uris[estado])
        return f"▶️ Reproduciendo playlist {estado}", 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
