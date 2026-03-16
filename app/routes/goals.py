from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for

from app import db
from app.models import Goal

bp = Blueprint("goals", __name__)


@bp.route("/")
def index():
    goals = Goal.query.order_by(Goal.date_echeance.asc().nullslast()).all()
    return render_template("goals.html", goals=goals)


@bp.route("/add", methods=["POST"])
def add():
    echeance = request.form.get("date_echeance")
    goal = Goal(
        titre=request.form["titre"],
        description=request.form.get("description", ""),
        valeur_cible=float(request.form.get("valeur_cible", 100)),
        valeur_actuelle=float(request.form.get("valeur_actuelle", 0)),
        unite=request.form.get("unite", "%"),
        date_echeance=datetime.fromisoformat(echeance) if echeance else None,
        couleur=request.form.get("couleur", "#10b981"),
    )
    db.session.add(goal)
    db.session.commit()
    return redirect(url_for("goals.index"))


@bp.route("/update/<int:goal_id>", methods=["POST"])
def update(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    goal.valeur_actuelle = float(request.form["valeur_actuelle"])
    db.session.commit()
    return redirect(url_for("goals.index"))


@bp.route("/delete/<int:goal_id>", methods=["POST"])
def delete(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    db.session.delete(goal)
    db.session.commit()
    return redirect(url_for("goals.index"))
