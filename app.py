from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key"  # change ceci

# --- Base de données ---
def init_db():
    with sqlite3.connect("users.db") as db:
        c = db.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            content TEXT,
            timestamp TEXT
        )""")
        db.commit()

init_db()

# --- Routes ---

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with sqlite3.connect("users.db") as db:
            c = db.cursor()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                db.commit()
                return redirect("/login")
            except sqlite3.IntegrityError:
                return "Nom déjà pris, choisis-en un autre."
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with sqlite3.connect("users.db") as db:
            c = db.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
        if user:
            session["user"] = username
            return redirect("/chat")
        else:
            return "Nom ou mot de passe incorrect."
    return render_template("login.html")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/login")
    return render_template("chat.html", username=session["user"])

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# --- API pour le chat ---

@app.route("/send", methods=["POST"])
def send_message():
    if "user" not in session:
        return "Unauthorized", 403
    content = request.form["content"]
    with sqlite3.connect("users.db") as db:
        c = db.cursor()
        c.execute("INSERT INTO messages (username, content, timestamp) VALUES (?, ?, ?)",
                  (session["user"], content, datetime.now().strftime("%H:%M")))
        db.commit()
    return "OK"

@app.route("/messages")
def get_messages():
    with sqlite3.connect("users.db") as db:
        c = db.cursor()
        c.execute("SELECT username, content, timestamp FROM messages ORDER BY id DESC LIMIT 20")
        data = c.fetchall()
    return jsonify(list(reversed(data)))

if __name__ == "__main__":
    app.run(debug=True)
