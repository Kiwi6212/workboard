from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request, redirect, url_for

from app import db
from app.models import Event

bp = Blueprint("planning", __name__)


@bp.route("/")
def index():
    # Determine the week to display
    week_str = request.args.get("week")
    if week_str:
        try:
            start = datetime.strptime(week_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            start = _monday(datetime.now(timezone.utc))
    else:
        start = _monday(datetime.now(timezone.utc))
    end = start + timedelta(days=7)

    events = Event.query.filter(Event.date_debut >= start, Event.date_debut < end).order_by(Event.date_debut).all()

    days = []
    for i in range(7):
        day = start + timedelta(days=i)
        day_events = [e for e in events if e.date_debut.date() == day.date()]
        days.append((day, day_events))

    prev_week = (start - timedelta(days=7)).strftime("%Y-%m-%d")
    next_week = (start + timedelta(days=7)).strftime("%Y-%m-%d")

    return render_template("planning.html", days=days, prev_week=prev_week, next_week=next_week, start=start)


@bp.route("/add", methods=["POST"])
def add():
    event = Event(
        titre=request.form["titre"],
        description=request.form.get("description", ""),
        date_debut=datetime.fromisoformat(request.form["date_debut"]),
        date_fin=datetime.fromisoformat(request.form["date_fin"]),
        type=request.form.get("type", "tache"),
        couleur=request.form.get("couleur", "#3b82f6"),
    )
    db.session.add(event)
    db.session.commit()
    return redirect(url_for("planning.index"))


@bp.route("/delete/<int:event_id>", methods=["POST"])
def delete(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for("planning.index"))


def _monday(dt):
    return (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
