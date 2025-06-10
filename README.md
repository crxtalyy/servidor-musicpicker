# MusicPicker 🎵

Aplicación web para controlar música según tu ritmo cardíaco (BPM) usando Spotify.

## 🔗 URL Pública

Accedé a la app en: [https://musicpicker.onrender.com](https://musicpicker.onrender.com)

## 🧠 ¿Cómo funciona?

1. Iniciás sesión con tu cuenta Spotify.
2. Enviás BPM desde tu dispositivo (ej: Raspberry Pi).
3. La app elige una playlist según el BPM y empieza a reproducir.

## 📡 Endpoint para Raspberry Pi

- Método: `POST`
- URL: `https://musicpicker.onrender.com/play`
- Cuerpo JSON:
```json
{
  "bpm": 90
}