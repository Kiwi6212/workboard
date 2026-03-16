import os

from flask import Flask, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    # --- Auth middleware ---
    @app.before_request
    def check_auth():
        if request.endpoint and request.endpoint in ("login", "static"):
            return
        token = app.config["WB_TOKEN"]
        if request.cookies.get("wb_session") != token:
            return redirect(url_for("login"))

    @app.route("/login")
    def login():
        token = request.args.get("token", "")
        if token == app.config["WB_TOKEN"]:
            resp = make_response(redirect(url_for("dashboard.index")))
            resp.set_cookie("wb_session", token, httponly=True, samesite="Lax", max_age=86400 * 30)
            return resp
        return "<h1>WorkBoard — Login</h1><p>Append <code>?token=YOUR_TOKEN</code> to this URL.</p>", 401

    # --- Register blueprints ---
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.planning import bp as planning_bp
    from app.routes.tasks import bp as tasks_bp
    from app.routes.docs import bp as docs_bp
    from app.routes.notes import bp as notes_bp
    from app.routes.goals import bp as goals_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(planning_bp, url_prefix="/planning")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(docs_bp, url_prefix="/docs")
    app.register_blueprint(notes_bp, url_prefix="/notes")
    app.register_blueprint(goals_bp, url_prefix="/goals")

    with app.app_context():
        db.create_all()

    return app
