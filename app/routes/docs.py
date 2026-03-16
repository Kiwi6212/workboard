import os
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, current_app, abort
from werkzeug.utils import secure_filename

from app import db
from app.models import Document

bp = Blueprint("docs", __name__)


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


@bp.route("/")
def index():
    categorie = request.args.get("categorie")
    query = Document.query.order_by(Document.date_ajout.desc())
    if categorie:
        query = query.filter_by(categorie=categorie)
    documents = query.all()
    return render_template("docs.html", documents=documents, current_cat=categorie)


@bp.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        return redirect(url_for("docs.index"))
    if not _allowed(file.filename):
        abort(400, "Type de fichier non autorisé.")

    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
    file.save(path)

    doc = Document(
        nom_original=original,
        chemin=stored_name,
        categorie=request.form.get("categorie", "autre"),
        taille=os.path.getsize(path),
    )
    db.session.add(doc)
    db.session.commit()
    return redirect(url_for("docs.index"))


@bp.route("/view/<int:doc_id>")
def view(doc_id):
    doc = Document.query.get_or_404(doc_id)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], doc.chemin)


@bp.route("/delete/<int:doc_id>", methods=["POST"])
def delete(doc_id):
    doc = Document.query.get_or_404(doc_id)
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], doc.chemin)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(doc)
    db.session.commit()
    return redirect(url_for("docs.index"))
