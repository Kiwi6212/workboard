from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template

from app import db
from app.models import Intervention, Task, Event, Goal

bp = Blueprint("stats", __name__)


@bp.route("/")
def index():
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # --- Interventions par type ---
    types = ["reseau", "materiel", "logiciel", "imprimante", "autre"]
    interventions_par_type = {}
    for t in types:
        interventions_par_type[t] = Intervention.query.filter_by(type_probleme=t).count()

    # --- Interventions par mois (6 derniers mois) ---
    interventions_par_mois = []
    for i in range(5, -1, -1):
        d = now - timedelta(days=i * 30)
        m_start = d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if m_start.month == 12:
            m_end = m_start.replace(year=m_start.year + 1, month=1)
        else:
            m_end = m_start.replace(month=m_start.month + 1)
        count = Intervention.query.filter(
            Intervention.date_creation >= m_start,
            Intervention.date_creation < m_end,
        ).count()
        interventions_par_mois.append({
            "label": m_start.strftime("%b %Y"),
            "count": count,
        })

    # --- Temps moyen résolution ---
    resolved = db.session.query(db.func.avg(Intervention.duree_minutes)).filter(
        Intervention.statut == "resolu",
        Intervention.duree_minutes.isnot(None),
    ).scalar()
    temps_moyen_resolution = round(resolved) if resolved else 0

    # --- Taux de résolution ---
    total_interv = Intervention.query.count()
    resolu_count = Intervention.query.filter_by(statut="resolu").count()
    taux_resolution = round(resolu_count / total_interv * 100) if total_interv else 0

    # --- Interventions ce mois ---
    interv_ce_mois = Intervention.query.filter(Intervention.date_creation >= month_start).count()

    # --- Tâches complétées par semaine (4 dernières semaines) ---
    taches_par_semaine = []
    for i in range(3, -1, -1):
        w_start = now - timedelta(weeks=i, days=now.weekday())
        w_start = w_start.replace(hour=0, minute=0, second=0, microsecond=0)
        w_end = w_start + timedelta(days=7)
        count = Task.query.filter(
            Task.statut == "done",
            Task.date_creation >= w_start,
            Task.date_creation < w_end,
        ).count()
        taches_par_semaine.append({
            "label": "Sem. " + w_start.strftime("%d/%m"),
            "count": count,
        })

    # --- Temps total tâches ---
    total_sec = db.session.query(db.func.sum(Task.temps_passe_sec)).scalar() or 0
    temps_total_h = total_sec // 3600
    temps_total_m = (total_sec % 3600) // 60

    # --- Événements par type ---
    event_types = ["cours", "tache", "perso", "alternance"]
    evenements_par_type = {}
    for t in event_types:
        evenements_par_type[t] = Event.query.filter_by(type=t).count()

    # --- Objectifs progression ---
    goals = Goal.query.all()
    objectifs_progression = []
    for g in goals:
        pct = round(g.valeur_actuelle / g.valeur_cible * 100) if g.valeur_cible else 0
        objectifs_progression.append({
            "titre": g.titre,
            "valeur_actuelle": g.valeur_actuelle,
            "valeur_cible": g.valeur_cible,
            "unite": g.unite,
            "pourcentage": min(pct, 100),
        })

    return render_template(
        "stats.html",
        interv_ce_mois=interv_ce_mois,
        temps_moyen_resolution=temps_moyen_resolution,
        taux_resolution=taux_resolution,
        temps_total_h=temps_total_h,
        temps_total_m=temps_total_m,
        interventions_par_type=interventions_par_type,
        interventions_par_mois=interventions_par_mois,
        evenements_par_type=evenements_par_type,
        taches_par_semaine=taches_par_semaine,
        objectifs_progression=objectifs_progression,
    )
