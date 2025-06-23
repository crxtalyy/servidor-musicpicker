import time
import threading
import random
from spotipy import Spotify
from auth import get_token_info

playlist_uris = {
    "relajado": "spotify:playlist:2ObbFHzjAw5yucJ57MbqOn",
    "normal":   "spotify:playlist:37i9dQZF1DWSoyxGghlqv5",
    "agitado":  "spotify:playlist:37i9dQZF1EIgSjgoYBB2M6"
}

ultimo_bpm = None
bpm_timestamp = None
estado_actual = None

def actualizar_bpm(bpm):
    global ultimo_bpm, bpm_timestamp
    ultimo_bpm = bpm
    bpm_timestamp = time.time()

def reproducir_playlist_aleatoria(sp, playlist_uri):
    try:
        playlist = sp.playlist(playlist_uri)
        total_tracks = playlist['tracks']['total']
        if total_tracks == 0:
            print("⚠️ Playlist vacía.")
            return

        random_index = random.randint(0, total_tracks - 1)
        sp.start_playback(context_uri=playlist_uri, offset={'position': random_index})
        print(f"🎶 Reproduciendo canción aleatoria (posición {random_index}) en {playlist_uri}")
    except Exception as e:
        print(f"❌ Error al reproducir playlist aleatoria: {e}")

def reproductor_autonomo():
    global ultimo_bpm, bpm_timestamp, estado_actual

    while True:
        now = time.time()

        if not ultimo_bpm or not bpm_timestamp:
            time.sleep(2)
            continue

        if now - bpm_timestamp > 30:
            print("⏳ Sin BPM recientes. Pausando análisis.")
            time.sleep(2)
            continue

        token_info = get_token_info()
        if not token_info:
            time.sleep(2)
            continue

        sp = Spotify(auth=token_info["access_token"])

        try:
            current = sp.current_playback()
            if not current:
                time.sleep(2)
                continue

            if not current["is_playing"]:
                print("⏸️ Música pausada manualmente. No se cambia playlist.")
                time.sleep(5)
                continue

            bpm = ultimo_bpm
            if bpm < 75:
                nuevo_estado = "relajado"
            elif bpm <= 110:
                nuevo_estado = "normal"
            else:
                nuevo_estado = "agitado"

            if nuevo_estado != estado_actual:
                duracion = current["item"]["duration_ms"]
                progreso = current["progress_ms"]

                if progreso >= duracion - 1000:
                    playlist_uri = playlist_uris[nuevo_estado]
                    reproducir_playlist_aleatoria(sp, playlist_uri)
                    estado_actual = nuevo_estado
                    print(f"▶️ [Cambio de estado] a {nuevo_estado}: {playlist_uri}")

        except Exception as e:
            print(f"❌ Error en reproducción automática: {e}")

        time.sleep(5)

def iniciar_reproductor():
    hilo = threading.Thread(target=reproductor_autonomo, daemon=True)
    hilo.start()