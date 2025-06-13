# app.py

from flask import Flask, redirect
from auth import sp_oauth, token_info
from bpm_handler import bpm_blueprint
from auto_player import iniciar_reproductor

import os

app = Flask(__name__)
app.register_blueprint(bpm_blueprint)

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

if __name__ == "__main__":
    iniciar_reproductor()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)