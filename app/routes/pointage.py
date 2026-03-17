import csv
import io
from datetime import date, datetime, time, timezone

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, Response

from app import db
from app.models import Pointage, HeureSup

bp = Blueprint("pointage", __name__)


@bp.route("/")
def index():
    today = date.today()
    pointage_today = Pointage.query.filter_by(date=today).first()

    # Last 30 pointages
    recent = Pointage.query.order_by(Pointage.date.desc()).limit(30).all()

    # Monthly summary
    month_start = today.replace(day=1)
    pointages_mois = Pointage.query.filter(Pointage.date >= month_start).all()
    heures_reelles = sum(p.heures_travaillees or 0 for p in pointages_mois)

    # Working days this month (Mon-Fri up to today)
    jours_travailles = 0
    d = month_start
    while d <= today:
        if d.weekday() < 5:  # Mon-Fri
            jours_travailles += 1
        d = d.replace(day=d.day + 1) if d.day < 28 else _next_day(d)
    heures_theoriques = jours_travailles * 7

    # Overtime this month
    heures_sup_mois = HeureSup.query.filter(HeureSup.date >= month_start).all()
    total_sup_minutes = sum(h.duree_minutes for h in heures_sup_mois)

    solde = heures_reelles - heures_theoriques

    # All overtime entries (recent)
    all_heures_sup = HeureSup.query.order_by(HeureSup.date.desc()).limit(20).all()

    # Available months for export (current + 3 previous)
    export_months = []
    for i in range(4):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        export_months.append((y, m, f"{_month_name(m)} {y}"))

    return render_template(
        "pointage.html",
        pointage_today=pointage_today,
        recent=recent,
        heures_theoriques=heures_theoriques,
        heures_reelles=round(heures_reelles, 2),
        total_sup_minutes=total_sup_minutes,
        solde=round(solde, 2),
        all_heures_sup=all_heures_sup,
        export_months=export_months,
        today=today,
    )


def _next_day(d):
    """Helper to increment date safely across month boundaries."""
    from datetime import timedelta
    return d + timedelta(days=1)


def _month_name(m):
    names = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
             "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    return names[m]


@bp.route("/arrivee", methods=["POST"])
def arrivee():
    today = date.today()
    existing = Pointage.query.filter_by(date=today).first()
    if existing:
        # Already clocked in today — update arrival time
        existing.heure_arrivee = datetime.now().time().replace(second=0, microsecond=0)
        db.session.commit()
        return jsonify(ok=True, heure=existing.heure_arrivee.strftime("%H:%M"))

    pointage = Pointage(
        date=today,
        heure_arrivee=datetime.now().time().replace(second=0, microsecond=0),
    )
    db.session.add(pointage)
    db.session.commit()
    return jsonify(ok=True, heure=pointage.heure_arrivee.strftime("%H:%M"))


@bp.route("/depart", methods=["POST"])
def depart():
    today = date.today()
    pointage = Pointage.query.filter_by(date=today).first()
    if not pointage:
        return jsonify(ok=False, error="Aucune arrivée pointée aujourd'hui"), 400

    pointage.heure_depart = datetime.now().time().replace(second=0, microsecond=0)
    pointage.calculer_heures()
    db.session.commit()
    return jsonify(
        ok=True,
        heure=pointage.heure_depart.strftime("%H:%M"),
        heures_travaillees=pointage.heures_travaillees,
    )


@bp.route("/manuel", methods=["POST"])
def manuel():
    date_str = request.form.get("date")
    arrivee_str = request.form.get("heure_arrivee")
    depart_str = request.form.get("heure_depart")
    pause = int(request.form.get("pause_minutes", 60))
    notes = request.form.get("notes", "")

    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    h_arrivee = datetime.strptime(arrivee_str, "%H:%M").time()
    h_depart = datetime.strptime(depart_str, "%H:%M").time() if depart_str else None

    existing = Pointage.query.filter_by(date=d).first()
    if existing:
        existing.heure_arrivee = h_arrivee
        existing.heure_depart = h_depart
        existing.pause_minutes = pause
        existing.notes = notes
        existing.calculer_heures()
    else:
        p = Pointage(
            date=d,
            heure_arrivee=h_arrivee,
            heure_depart=h_depart,
            pause_minutes=pause,
            notes=notes,
        )
        p.calculer_heures()
        db.session.add(p)
    db.session.commit()
    return redirect(url_for("pointage.index"))


@bp.route("/heures-sup/new", methods=["POST"])
def new_heures_sup():
    date_str = request.form.get("date")
    duree = int(request.form.get("duree_minutes", 0))
    motif = request.form.get("motif", "")

    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    hs = HeureSup(date=d, duree_minutes=duree, motif=motif)
    db.session.add(hs)
    db.session.commit()
    return redirect(url_for("pointage.index"))


@bp.route("/export/<int:annee>/<int:mois>")
def export_csv(annee, mois):
    from calendar import monthrange
    start = date(annee, mois, 1)
    end = date(annee, mois, monthrange(annee, mois)[1])
    pointages = Pointage.query.filter(
        Pointage.date >= start, Pointage.date <= end
    ).order_by(Pointage.date).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Date", "Arrivée", "Départ", "Pause (min)", "Heures travaillées", "Notes"])
    for p in pointages:
        writer.writerow([
            p.date.strftime("%d/%m/%Y"),
            p.heure_arrivee.strftime("%H:%M") if p.heure_arrivee else "",
            p.heure_depart.strftime("%H:%M") if p.heure_depart else "",
            p.pause_minutes,
            p.heures_travaillees or "",
            p.notes or "",
        ])

    filename = f"pointage_{annee}_{mois:02d}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
