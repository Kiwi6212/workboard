from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, jsonify

from app import db, csrf
from app.models import Note

bp = Blueprint("notes", __name__)


@bp.route("/")
def index():
    notes = Note.query.order_by(Note.date_modif.desc()).all()
    return render_template("notes.html", notes=notes)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        note = Note(titre=request.form["titre"], contenu_md=request.form.get("contenu_md", ""))
        db.session.add(note)
        db.session.commit()
        return redirect(url_for("notes.edit", note_id=note.id))
    return render_template("note_edit.html", note=None)


@bp.route("/edit/<int:note_id>", methods=["GET", "POST"])
def edit(note_id):
    note = Note.query.get_or_404(note_id)
    if request.method == "POST":
        note.titre = request.form["titre"]
        note.contenu_md = request.form.get("contenu_md", "")
        note.date_modif = datetime.now(timezone.utc)
        db.session.commit()
        return redirect(url_for("notes.index"))
    return render_template("note_edit.html", note=note)


@bp.route("/autosave/<int:note_id>", methods=["POST"])
@csrf.exempt
def autosave(note_id):
    note = Note.query.get_or_404(note_id)
    data = request.get_json()
    note.contenu_md = data.get("contenu_md", note.contenu_md)
    note.titre = data.get("titre", note.titre)
    note.date_modif = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(ok=True)


@bp.route("/delete/<int:note_id>", methods=["POST"])
def delete(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("notes.index"))
