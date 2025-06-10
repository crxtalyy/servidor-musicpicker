from flask import Flask, render_template, session, redirect, request
from auth import login, callback
from bpm_handler import recibir_bpm

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login")
def spotify_login():
    return login()

@app.route("/callback")
def spotify_callback():
    return callback()

@app.route("/dashboard")
def dashboard():
    if "token_info" not in session:
        return redirect("/")
    return render_template("dashboard.html", user_id=session.get("user_id"))

@app.route("/play", methods=["POST"])
def play():
    return recibir_bpm()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))