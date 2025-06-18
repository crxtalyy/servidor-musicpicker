from flask import Blueprint, request, jsonify
from spotipy import Spotify
from auth import get_token_info
from auto_player import actualizar_bpm

bpm_blueprint = Blueprint("bpm", __name__)

@bpm_blueprint.route("/bpm", methods=["POST"])
def recibir_bpm():
    data = request.get_json()
    if not data or "bpm" not in data:
        return jsonify({"error": "Se requiere el valor 'bpm'"}), 400

    try:
        bpm = int(data.get("bpm"))
        if bpm <= 0:
            return jsonify({"error": "BPM inválido"}), 400

        actualizar_bpm(bpm)  # Actualiza el BPM global

        token_info = get_token_info()
        if not token_info:
            return jsonify({"error": "Token inválido"}), 403

        sp = Spotify(auth=token_info["access_token"])

        # Verificamos si ya hay algo reproduciéndose
        current = sp.current_playback()
        if current and current.get("is_playing"):
            print(f"🔄 Ya se está reproduciendo algo. BPM recibido: {bpm}")
            return jsonify({"message": "🎵 Ya hay una canción reproduciéndose"}), 200

        # Determinar el estado según BPM
        if bpm < 75:
            categoria = "relajado"
        elif bpm <= 110:
            categoria = "normal"
        else:
            categoria = "agitado"

        playlist_uris = {
            "relajado": "spotify:playlist:2ObbFHzjAw5yucJ57MbqOn",
            "normal":   "spotify:playlist:37i9dQZF1DWSoyxGghlqv5",
            "agitado":  "spotify:playlist:37i9dQZF1EIgSjgoYBB2M6"
        }

        # Reproducir la playlist correspondiente
        sp.start_playback(context_uri=playlist_uris[categoria])
        print(f"▶️ [Manual] Reproduciendo playlist para BPM {bpm} (estado: {categoria})")

        return jsonify({
            "message": f"▶️ Reproduciendo playlist de estado '{categoria}' para BPM {bpm}"
        }), 200

    except Exception as e:
        print(f"❌ Error en /bpm: {e}")
        return jsonify({"error": str(e)}), 500
