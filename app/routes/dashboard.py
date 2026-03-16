from datetime import datetime, timezone

from flask import Blueprint, render_template

from app.models import Task, Event, Note, Goal

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    now = datetime.now(timezone.utc)
    todo = Task.query.filter_by(statut="todo").count()
    in_progress = Task.query.filter_by(statut="in_progress").count()
    done = Task.query.filter_by(statut="done").count()
    upcoming_events = Event.query.filter(Event.date_debut >= now).order_by(Event.date_debut).limit(3).all()
    recent_notes = Note.query.order_by(Note.date_modif.desc()).limit(3).all()
    goals = Goal.query.all()
    return render_template(
        "dashboard.html",
        todo=todo,
        in_progress=in_progress,
        done=done,
        upcoming_events=upcoming_events,
        recent_notes=recent_notes,
        goals=goals,
    )
