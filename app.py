from flask import Flask, redirect, request, render_template  # Import render_template para las vistas
from auth import sp_oauth, set_token_info
from bpm_handler import bpm_blueprint
from auto_player import iniciar_reproductor

import os

app = Flask(__name__)
app.register_blueprint(bpm_blueprint)

@app.route("/")
def home():
    # Mostrar la página de login con el botón, usando template
    return render_template("login.html")

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    set_token_info(token_info)
    # En lugar de solo texto, redirigimos a dashboard o mostramos la plantilla
    return render_template("dashboard.html", user_id=token_info.get("id", "desconocido"))

if __name__ == "__main__":
    iniciar_reproductor()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
