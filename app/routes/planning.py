from datetime import datetime, timedelta, timezone, date
import calendar

from flask import Blueprint, render_template, request, redirect, url_for, jsonify

from app import db
from app.models import Event

bp = Blueprint("planning", __name__)

TYPE_COLORS = {
    "cours": "#4A90D9",
    "alternance": "#7c6de8",
    "tache": "#F5A623",
    "perso": "#27AE60",
}


def _naive(dt):
    """Strip timezone info from a datetime so all comparisons are naive."""
    if dt and dt.tzinfo:
        return dt.replace(tzinfo=None)
    return dt


@bp.route("/")
def index():
    view = request.args.get("view", "week")

    if view == "month":
        return _month_view()
    return _week_view()


def _week_view():
    week_str = request.args.get("week")
    if week_str:
        try:
            start = datetime.strptime(week_str, "%Y-%m-%d")
        except ValueError:
            start = _monday(datetime.now())
    else:
        start = _monday(datetime.now())

    end = start + timedelta(days=7)

    # Fetch events that overlap the week: date_debut < week_end AND date_fin >= week_start
    events = Event.query.filter(
        Event.date_debut < end,
        Event.date_fin >= start,
    ).order_by(Event.date_debut).all()

    days = []
    for i in range(7):
        day_start = start + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        day_events = []
        for e in events:
            ev_debut = _naive(e.date_debut)
            ev_fin = _naive(e.date_fin)
            if ev_debut < day_end and ev_fin >= day_start:
                color = TYPE_COLORS.get(e.type, e.couleur)
                is_multiday = ev_debut.date() != ev_fin.date()
                is_first_day = ev_debut.date() == day_start.date()
                is_last_day = ev_fin.date() == day_start.date()
                # Clamp times to this day
                ev_start = max(ev_debut, day_start)
                ev_end = min(ev_fin, day_end)
                day_events.append({
                    "event": e,
                    "color": color,
                    "is_multiday": is_multiday,
                    "is_first_day": is_first_day,
                    "is_last_day": is_last_day,
                    "start_hour": ev_start.hour + ev_start.minute / 60,
                    "end_hour": ev_end.hour + ev_end.minute / 60 if ev_end.date() == day_start.date() else 20,
                })
        days.append((day_start, day_events))

    prev_week = (start - timedelta(days=7)).strftime("%Y-%m-%d")
    next_week = (start + timedelta(days=7)).strftime("%Y-%m-%d")
    now = datetime.now()

    return render_template(
        "planning.html",
        days=days,
        prev_week=prev_week,
        next_week=next_week,
        start=start,
        view="week",
        now=now,
        type_colors=TYPE_COLORS,
    )


def _month_view():
    month_str = request.args.get("month")
    if month_str:
        try:
            year, month = int(month_str[:4]), int(month_str[5:7])
        except (ValueError, IndexError):
            today = datetime.now()
            year, month = today.year, today.month
    else:
        today = datetime.now()
        year, month = today.year, today.month

    first_day = date(year, month, 1)
    # Monday-based: get the Monday of the first week
    start_offset = first_day.weekday()  # 0=Mon
    grid_start = first_day - timedelta(days=start_offset)

    # 6 weeks grid
    grid_end = grid_start + timedelta(days=42)

    dt_start = datetime(grid_start.year, grid_start.month, grid_start.day)
    dt_end = datetime(grid_end.year, grid_end.month, grid_end.day)

    events = Event.query.filter(
        Event.date_debut < dt_end,
        Event.date_fin >= dt_start,
    ).order_by(Event.date_debut).all()

    weeks = []
    for w in range(6):
        week = []
        for d in range(7):
            day = grid_start + timedelta(days=w * 7 + d)
            day_dt_start = datetime(day.year, day.month, day.day)
            day_dt_end = day_dt_start + timedelta(days=1)
            day_events = []
            for e in events:
                ev_debut = _naive(e.date_debut)
                ev_fin = _naive(e.date_fin)
                if ev_debut < day_dt_end and ev_fin >= day_dt_start:
                    color = TYPE_COLORS.get(e.type, e.couleur)
                    day_events.append({"event": e, "color": color})
            week.append({
                "date": day,
                "in_month": day.month == month,
                "events": day_events[:3],
                "overflow": max(0, len(day_events) - 3),
                "week_start": (day - timedelta(days=day.weekday())).strftime("%Y-%m-%d"),
            })
        weeks.append(week)

    month_names = [
        "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
    ]

    prev_m = month - 1 if month > 1 else 12
    prev_y = year if month > 1 else year - 1
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1

    now = datetime.now()

    return render_template(
        "planning.html",
        view="month",
        weeks=weeks,
        month_name=month_names[month],
        year=year,
        prev_month=f"{prev_y}-{prev_m:02d}",
        next_month=f"{next_y}-{next_m:02d}",
        type_colors=TYPE_COLORS,
        # Provide dummies for week view variables used in template
        days=[],
        prev_week="",
        next_week="",
        start=now,
        now=now,
    )


@bp.route("/add", methods=["POST"])
def add():
    ev_type = request.form.get("type", "tache")
    color = TYPE_COLORS.get(ev_type, request.form.get("couleur", "#3b82f6"))
    event = Event(
        titre=request.form["titre"],
        description=request.form.get("description", ""),
        date_debut=datetime.fromisoformat(request.form["date_debut"]),
        date_fin=datetime.fromisoformat(request.form["date_fin"]),
        type=ev_type,
        couleur=color,
    )
    db.session.add(event)
    db.session.commit()
    return redirect(request.referrer or url_for("planning.index"))


@bp.route("/delete/<int:event_id>", methods=["POST"])
def delete(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return redirect(request.referrer or url_for("planning.index"))


def _monday(dt):
    return (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
