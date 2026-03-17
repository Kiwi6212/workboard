from datetime import datetime, timezone, date

from flask import Blueprint, render_template

from app.models import Task, Event, Note, Goal, Intervention, Pointage

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
    # Recent active tasks (todo or in_progress)
    recent_tasks = Task.query.filter(
        Task.statut.in_(["todo", "in_progress"])
    ).order_by(Task.date_creation.desc()).limit(3).all()
    # Interventions stats (current month)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    interv_total = Intervention.query.filter(Intervention.date_creation >= month_start).count()
    interv_urgent = Intervention.query.filter(
        Intervention.date_creation >= month_start, Intervention.priorite == "urgent"
    ).count()
    interv_resolu = Intervention.query.filter(
        Intervention.date_creation >= month_start, Intervention.statut == "resolu"
    ).count()
    recent_interventions = Intervention.query.filter(
        Intervention.date_creation >= month_start
    ).order_by(Intervention.date_creation.desc()).limit(3).all()
    # Pointage du jour
    pointage_today = Pointage.query.filter_by(date=date.today()).first()
    return render_template(
        "dashboard.html",
        todo=todo,
        in_progress=in_progress,
        done=done,
        upcoming_events=upcoming_events,
        recent_notes=recent_notes,
        goals=goals,
        recent_tasks=recent_tasks,
        interv_total=interv_total,
        interv_urgent=interv_urgent,
        interv_resolu=interv_resolu,
        recent_interventions=recent_interventions,
        pointage_today=pointage_today,
    )
