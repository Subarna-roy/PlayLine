import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "playline.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("PLAYLINE_SECRET", "change-this-secret-key-before-deployment")

GAMES = [
    {"slug": "tic-tac-toe", "name": "Tic Tac Toe", "category": "Strategy", "description": "Challenge a friend in the classic three-in-a-row game.", "icon": "✕", "color": "pink", "difficulty": "Easy"},
    {"slug": "snake", "name": "Neon Snake", "category": "Arcade", "description": "Collect glowing orbs, grow longer and avoid the walls.", "icon": "🐍", "color": "green", "difficulty": "Medium"},
    {"slug": "2048", "name": "2048", "category": "Puzzle", "description": "Slide numbered tiles and combine them to reach 2048.", "icon": "²", "color": "purple", "difficulty": "Medium"},
    {"slug": "rock-paper-scissors", "name": "Rock Paper Scissors", "category": "Casual", "description": "Make your move and see if you can beat the computer.", "icon": "✊", "color": "blue", "difficulty": "Easy"},
    {"slug": "memory-match", "name": "Memory Match", "category": "Puzzle", "description": "Flip cards and find all matching pairs.", "icon": "◈", "color": "orange", "difficulty": "Easy"},
    {"slug": "number-guessing", "name": "Number Guessing", "category": "Brain", "description": "Use the hints to find the hidden number in fewer attempts.", "icon": "?", "color": "cyan", "difficulty": "Easy"},
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_slug TEXT NOT NULL,
            score INTEGER NOT NULL DEFAULT 0,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_slug TEXT NOT NULL,
            UNIQUE(user_id, game_slug),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)

def current_user():
    if "user_id" not in session:
        return None
    with get_db() as db:
        return db.execute("SELECT id, username, email FROM users WHERE id = ?", (session["user_id"],)).fetchone()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_globals():
    return {"current_user": current_user(), "games": GAMES}

@app.route("/")
def index():
    if current_user():
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 6 or "@" not in email:
            flash("Use a username of at least 3 characters, a valid email and a password of at least 6 characters.", "error")
            return render_template("register.html")
        try:
            with get_db() as db:
                cur = db.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                                 (username, email, generate_password_hash(password)))
                session["user_id"] = cur.lastrowid
            flash("Account created. Welcome to Playline!", "success")
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("That username or email is already registered.", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE username = ? OR email = ?", (identity, identity.lower())).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            flash("You are now logged in.", "success")
            return redirect(url_for("dashboard"))
        flash("Incorrect username/email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    with get_db() as db:
        stats = db.execute("""
            SELECT COUNT(*) AS plays, COALESCE(SUM(score), 0) AS points,
                   COUNT(DISTINCT game_slug) AS games_played
            FROM scores WHERE user_id = ?
        """, (user["id"],)).fetchone()
        recent = db.execute("SELECT game_slug, score, played_at FROM scores WHERE user_id = ? ORDER BY id DESC LIMIT 5",
                            (user["id"],)).fetchall()
        favs = {r["game_slug"] for r in db.execute("SELECT game_slug FROM favorites WHERE user_id = ?", (user["id"],))}
    return render_template("dashboard.html", stats=stats, recent=recent, favorites=favs)

@app.route("/games")
@login_required
def game_library():
    query = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "All")
    filtered = [g for g in GAMES if (not query or query in g["name"].lower() or query in g["description"].lower())
                and (category == "All" or g["category"] == category)]
    with get_db() as db:
        favs = {r["game_slug"] for r in db.execute("SELECT game_slug FROM favorites WHERE user_id = ?", (current_user()["id"],))}
    return render_template("games.html", game_list=filtered, query=query, selected_category=category, favorites=favs)

@app.route("/play/<slug>")
@login_required
def play(slug):
    game = next((g for g in GAMES if g["slug"] == slug), None)
    if not game:
        flash("Game not found.", "error")
        return redirect(url_for("game_library"))
    return render_template("play.html", game=game)

@app.route("/api/score", methods=["POST"])
@login_required
def save_score():
    data = request.get_json(silent=True) or {}
    slug = data.get("game_slug")
    score = data.get("score")
    if slug not in [g["slug"] for g in GAMES] or not isinstance(score, int) or score < 0 or score > 1000000:
        return jsonify({"ok": False, "message": "Invalid score."}), 400
    with get_db() as db:
        db.execute("INSERT INTO scores (user_id, game_slug, score) VALUES (?, ?, ?)",
                   (current_user()["id"], slug, score))
    return jsonify({"ok": True, "message": "Score saved."})

@app.route("/favorite/<slug>", methods=["POST"])
@login_required
def favorite(slug):
    if slug not in [g["slug"] for g in GAMES]:
        return jsonify({"ok": False}), 404
    user_id = current_user()["id"]
    with get_db() as db:
        existing = db.execute("SELECT id FROM favorites WHERE user_id = ? AND game_slug = ?", (user_id, slug)).fetchone()
        if existing:
            db.execute("DELETE FROM favorites WHERE id = ?", (existing["id"],))
            state = False
        else:
            db.execute("INSERT OR IGNORE INTO favorites (user_id, game_slug) VALUES (?, ?)", (user_id, slug))
            state = True
    return jsonify({"ok": True, "favorite": state})

@app.route("/leaderboard")
@login_required
def leaderboard():
    with get_db() as db:
        rows = db.execute("""
            SELECT users.username, SUM(scores.score) AS points, COUNT(scores.id) AS plays
            FROM users JOIN scores ON users.id = scores.user_id
            GROUP BY users.id ORDER BY points DESC, plays DESC LIMIT 10
        """).fetchall()
    return render_template("leaderboard.html", rows=rows)

@app.route("/profile")
@login_required
def profile():
    user = current_user()
    with get_db() as db:
        stats = db.execute("SELECT COUNT(*) AS plays, COALESCE(SUM(score),0) AS points FROM scores WHERE user_id = ?",
                           (user["id"],)).fetchone()
    return render_template("profile.html", user=user, stats=stats)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
