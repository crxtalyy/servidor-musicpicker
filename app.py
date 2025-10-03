from flask import Flask, redirect, request, render_template
from auth import sp_oauth, set_token_info
from bpm_handler import bpm_blueprint
from auto_player import iniciar_reproductor
from spotipy import Spotify
import os

app = Flask(__name__)
app.register_blueprint(bpm_blueprint)

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code, as_dict=True)
    set_token_info(token_info)

    sp = Spotify(auth=token_info['access_token'])
    user_profile = sp.current_user()
    user_id = user_profile.get("id", "desconocido")

    return render_template("dashboard.html", user_id=user_id)

if __name__ == "__main__":
    iniciar_reproductor()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
