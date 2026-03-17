from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, jsonify

from app import db
from app.models import Intervention

bp = Blueprint("interventions", __name__)


@bp.route("/")
def index():
    en_attente = Intervention.query.filter_by(statut="en_attente").order_by(Intervention.date_creation.desc()).all()
    en_cours = Intervention.query.filter_by(statut="en_cours").order_by(Intervention.date_creation.desc()).all()
    resolues = Intervention.query.filter(
        Intervention.statut.in_(["resolu", "non_resolu"])
    ).order_by(Intervention.date_creation.desc()).all()
    return render_template(
        "interventions.html",
        en_attente=en_attente,
        en_cours=en_cours,
        resolues=resolues,
    )


@bp.route("/new", methods=["POST"])
def new():
    intervention = Intervention(
        titre=request.form["titre"],
        lieu=request.form.get("lieu", ""),
        demandeur=request.form.get("demandeur", ""),
        type_probleme=request.form.get("type_probleme", "autre"),
        type_intervention=request.form.get("type_intervention", "intervention"),
        priorite=request.form.get("priorite", "normal"),
        notes_solution=request.form.get("notes_solution", ""),
        duree_minutes=int(request.form["duree_minutes"]) if request.form.get("duree_minutes") else None,
    )
    db.session.add(intervention)
    db.session.commit()
    return redirect(url_for("interventions.index"))


@bp.route("/<int:id>/statut", methods=["POST"])
def change_statut(id):
    intervention = Intervention.query.get_or_404(id)
    data = request.get_json(silent=True)
    new_statut = data.get("statut") if data else request.form.get("statut")
    if new_statut in ("en_attente", "en_cours", "resolu", "non_resolu"):
        intervention.statut = new_statut
        if new_statut in ("resolu", "non_resolu"):
            intervention.date_resolution = datetime.now(timezone.utc)
        else:
            intervention.date_resolution = None
        db.session.commit()
    if data:
        return jsonify(ok=True)
    return redirect(url_for("interventions.index"))


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    intervention = Intervention.query.get_or_404(id)
    db.session.delete(intervention)
    db.session.commit()
    return redirect(url_for("interventions.index"))


@bp.route("/<int:id>")
def detail(id):
    intervention = Intervention.query.get_or_404(id)
    return render_template("intervention_detail.html", i=intervention)


@bp.route("/<int:id>/edit", methods=["POST"])
def edit(id):
    intervention = Intervention.query.get_or_404(id)
    intervention.titre = request.form.get("titre", intervention.titre)
    intervention.lieu = request.form.get("lieu", intervention.lieu)
    intervention.demandeur = request.form.get("demandeur", intervention.demandeur)
    intervention.type_probleme = request.form.get("type_probleme", intervention.type_probleme)
    intervention.type_intervention = request.form.get("type_intervention", intervention.type_intervention)
    intervention.priorite = request.form.get("priorite", intervention.priorite)
    intervention.notes_solution = request.form.get("notes_solution", intervention.notes_solution)
    intervention.duree_minutes = int(request.form["duree_minutes"]) if request.form.get("duree_minutes") else None
    db.session.commit()
    return redirect(url_for("interventions.detail", id=id))
