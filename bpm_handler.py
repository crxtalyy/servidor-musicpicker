from flask import request, session, jsonify
from spotipy import Spotify

playlist_uris = {
    "relajado": "spotify:playlist:2ObbFHzjAw5yucJ57MbqOn",
    "normal":   "spotify:playlist:37i9dQZF1DWSoyxGghlqv5",
    "agitado":  "spotify:playlist:37i9dQZF1EIgSjgoYBB2M6"
}

def recibir_bpm():
    data = request.json or {}
    bpm = int(data.get("bpm", 0))
    sp = None
    if session.get("token_info"):
        sp = Spotify(auth=session["token_info"]["access_token"])

    if not sp:
        return "❌ Usuario no autenticado", 401

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