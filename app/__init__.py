import os

import bcrypt
from flask import Flask, request, redirect, url_for, make_response, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()

LOGIN_PASSWORD_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion — WorkBoard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', system-ui, sans-serif; box-sizing: border-box; }
        body { background: linear-gradient(135deg, #0f0c29, #302b63); color: #e2e8f0; min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
        .card { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 32px; width: 380px; max-width: 90vw; }
        h1 { font-size: 1.3rem; font-weight: 700; margin: 0 0 4px; }
        .sub { color: rgba(255,255,255,0.4); font-size: 0.8rem; margin-bottom: 24px; }
        label { font-size: 0.75rem; color: rgba(255,255,255,0.4); display: block; margin-bottom: 4px; }
        input { width: 100%; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 10px 12px; font-size: 0.875rem; color: #e2e8f0; outline: none; margin-bottom: 14px; }
        input:focus { border-color: #7c6de8; box-shadow: 0 0 0 2px rgba(124,109,232,0.3); }
        button { width: 100%; background: #7c6de8; color: #fff; border: none; border-radius: 10px; padding: 10px; font-size: 0.875rem; font-weight: 500; cursor: pointer; }
        button:hover { background: #6a5dd4; }
        .error { background: rgba(239,68,68,0.15); color: #ef4444; padding: 8px 12px; border-radius: 8px; font-size: 0.8rem; margin-bottom: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>WorkBoard</h1>
        <p class="sub">Connectez-vous pour continuer</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">

            <label>Nom d'utilisateur</label>
            <input name="username" type="text" required autofocus>
            <label>Mot de passe</label>
            <input name="password" type="password" required>
            <button type="submit">Se connecter</button>
        </form>
    </div>
</body>
</html>
"""


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    PUBLIC_ENDPOINTS = ("login", "login_password", "static")

    # --- Auth middleware ---
    @app.before_request
    def check_auth():
        if request.endpoint and request.endpoint in PUBLIC_ENDPOINTS:
            return
        token = app.config["WB_TOKEN"]
        # Step 1: token cookie
        if request.cookies.get("wb_session") != token:
            qs_token = request.args.get("token")
            if qs_token:
                return redirect(url_for("login", token=qs_token))
            return redirect(url_for("login"))
        # Step 2: password auth (only if a hash is configured)
        if app.config["WB_PASSWORD_HASH"] and not session.get("authenticated"):
            if request.endpoint != "logout":
                return redirect(url_for("login_password"))

    @app.route("/login")
    def login():
        token = request.args.get("token", "")
        if token == app.config["WB_TOKEN"]:
            # If no password hash configured, authenticate directly
            if not app.config["WB_PASSWORD_HASH"]:
                session["authenticated"] = True
                resp = make_response(redirect(url_for("dashboard.index")))
            else:
                resp = make_response(redirect(url_for("login_password")))
            resp.set_cookie("wb_session", token, httponly=True, samesite="Lax", max_age=86400 * 30)
            return resp
        return "<h1>WorkBoard — Login</h1><p>Append <code>?token=YOUR_TOKEN</code> to this URL.</p>", 401

    @app.route("/login-password", methods=["GET", "POST"])
    @csrf.exempt
    def login_password():
        # If already authenticated, go to dashboard
        if session.get("authenticated"):
            return redirect(url_for("dashboard.index"))
        # Must have valid token cookie first
        if request.cookies.get("wb_session") != app.config["WB_TOKEN"]:
            return redirect(url_for("login"))

        error = None
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            pw_hash = app.config["WB_PASSWORD_HASH"].encode()
            if (
                username == app.config["WB_USERNAME"]
                and pw_hash
                and bcrypt.checkpw(password.encode(), pw_hash)
            ):
                session["authenticated"] = True
                return redirect(url_for("dashboard.index"))
            error = "Identifiants incorrects"
        return render_template_string(LOGIN_PASSWORD_HTML, error=error)

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        resp = make_response(redirect(url_for("login")))
        resp.delete_cookie("wb_session")
        return resp

    # --- Register blueprints ---
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.planning import bp as planning_bp
    from app.routes.tasks import bp as tasks_bp
    from app.routes.interventions import bp as interventions_bp
    from app.routes.docs import bp as docs_bp
    from app.routes.notes import bp as notes_bp
    from app.routes.goals import bp as goals_bp
    from app.routes.stats import bp as stats_bp
    from app.routes.pointage import bp as pointage_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(planning_bp, url_prefix="/planning")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(interventions_bp, url_prefix="/interventions")
    app.register_blueprint(docs_bp, url_prefix="/docs")
    app.register_blueprint(notes_bp, url_prefix="/notes")
    app.register_blueprint(goals_bp, url_prefix="/goals")
    app.register_blueprint(stats_bp, url_prefix="/stats")
    app.register_blueprint(pointage_bp, url_prefix="/pointage")

    with app.app_context():
        db.create_all()
        # Migrate: add timer columns to tasks if missing
        import sqlite3 as _sql
        _conn = db.engine.raw_connection()
        _cur = _conn.cursor()
        _cols = [r[1] for r in _cur.execute("PRAGMA table_info(tasks)").fetchall()]
        if "timer_running" not in _cols:
            _cur.execute("ALTER TABLE tasks ADD COLUMN timer_running BOOLEAN DEFAULT 0")
        if "timer_start" not in _cols:
            _cur.execute("ALTER TABLE tasks ADD COLUMN timer_start DATETIME")
        _conn.commit()
        _conn.close()

    return app
