from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, jsonify

from app import db, csrf
from app.models import Task

bp = Blueprint("tasks", __name__)


@bp.route("/")
def index():
    todo = Task.query.filter_by(statut="todo").order_by(Task.priorite.desc()).all()
    in_progress = Task.query.filter_by(statut="in_progress").order_by(Task.priorite.desc()).all()
    done = Task.query.filter_by(statut="done").order_by(Task.priorite.desc()).all()
    now_ts = datetime.now(timezone.utc).timestamp()
    return render_template("tasks.html", todo=todo, in_progress=in_progress, done=done, now_ts=now_ts)


@bp.route("/add", methods=["POST"])
def add():
    task = Task(
        titre=request.form["titre"],
        description=request.form.get("description", ""),
        priorite=int(request.form.get("priorite", 0)),
    )
    db.session.add(task)
    db.session.commit()
    return redirect(url_for("tasks.index"))


@bp.route("/status/<int:task_id>", methods=["POST"])
def update_status(task_id):
    task = Task.query.get_or_404(task_id)
    task.statut = request.form["statut"]
    db.session.commit()
    return redirect(url_for("tasks.index"))


@bp.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("tasks.index"))


@bp.route("/timer/<int:task_id>", methods=["POST"])
@csrf.exempt
def timer(task_id):
    """Legacy timer endpoint — kept for backwards compat."""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    seconds = int(data.get("seconds", 0))
    if 0 < seconds <= 3600:
        task.temps_passe_sec += seconds
        db.session.commit()
    return jsonify(temps_passe_sec=task.temps_passe_sec)


@bp.route("/<int:task_id>/timer/start", methods=["POST"])
@csrf.exempt
def timer_start(task_id):
    task = Task.query.get_or_404(task_id)
    if not task.timer_running:
        task.timer_running = True
        task.timer_start = datetime.now(timezone.utc)
        db.session.commit()
    return jsonify(ok=True, temps_passe_sec=task.temps_passe_sec,
                   timer_start=task.timer_start.timestamp())


@bp.route("/<int:task_id>/timer/stop", methods=["POST"])
@csrf.exempt
def timer_stop(task_id):
    task = Task.query.get_or_404(task_id)
    if task.timer_running and task.timer_start:
        elapsed = int((datetime.now(timezone.utc) - task.timer_start).total_seconds())
        task.temps_passe_sec += max(elapsed, 0)
        task.timer_running = False
        task.timer_start = None
        db.session.commit()
    return jsonify(ok=True, temps_passe_sec=task.temps_passe_sec)


@bp.route("/<int:task_id>/timer/add", methods=["POST"])
@csrf.exempt
def timer_add(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    hours = int(data.get("hours", 0))
    minutes = int(data.get("minutes", 0))
    seconds_to_add = hours * 3600 + minutes * 60
    if seconds_to_add > 0:
        task.temps_passe_sec += seconds_to_add
        db.session.commit()
    return jsonify(ok=True, temps_passe_sec=task.temps_passe_sec)


@bp.route("/<int:task_id>/timer/reset", methods=["POST"])
@csrf.exempt
def timer_reset(task_id):
    task = Task.query.get_or_404(task_id)
    task.temps_passe_sec = 0
    task.timer_running = False
    task.timer_start = None
    db.session.commit()
    return jsonify(ok=True, temps_passe_sec=0)


@bp.route("/<int:task_id>")
def detail(task_id):
    task = Task.query.get_or_404(task_id)
    now_ts = datetime.now(timezone.utc).timestamp()
    return render_template("task_detail.html", t=task, now_ts=now_ts)


@bp.route("/<int:task_id>/edit", methods=["POST"])
def edit(task_id):
    task = Task.query.get_or_404(task_id)
    task.titre = request.form["titre"]
    task.description = request.form.get("description", "")
    task.statut = request.form.get("statut", task.statut)
    task.priorite = int(request.form.get("priorite", task.priorite))
    db.session.commit()
    return redirect(url_for("tasks.detail", task_id=task.id))


@bp.route("/<int:task_id>/delete", methods=["POST"])
def delete_detail(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("tasks.index"))
