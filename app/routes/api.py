from datetime import date, datetime

from flask import Blueprint, jsonify, request

from app import db, csrf
from app.models import Note, Intervention, Task, Pointage

bp = Blueprint("api", __name__)


# ---------- DELETE endpoints ----------

@bp.route('/notes/<int:note_id>', methods=['DELETE'])
@csrf.exempt
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({"success": True, "message": "Note supprimée"})


@bp.route('/interventions/<int:intervention_id>', methods=['DELETE'])
@csrf.exempt
def delete_intervention(intervention_id):
    intervention = Intervention.query.get_or_404(intervention_id)
    db.session.delete(intervention)
    db.session.commit()
    return jsonify({"success": True, "message": "Intervention supprimée"})


@bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@csrf.exempt
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"success": True, "message": "Tâche supprimée"})


# ---------- PUT endpoints ----------

@bp.route('/tasks/<int:task_id>', methods=['PUT'])
@csrf.exempt
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    if 'titre' in data:
        task.titre = data['titre']
    if 'description' in data:
        task.description = data['description']
    if 'statut' in data and data['statut'] in ['todo', 'in_progress', 'done']:
        task.statut = data['statut']
    if 'priorite' in data:
        task.priorite = int(data['priorite'])
    db.session.commit()
    return jsonify({"success": True, "task": {
        "id": task.id, "titre": task.titre, "description": task.description,
        "statut": task.statut, "priorite": task.priorite
    }})


# ---------- POST endpoints ----------

@bp.route('/tasks/<int:task_id>/timer/add', methods=['POST'])
@csrf.exempt
def add_task_time(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    secondes = int(data.get('secondes', 0))
    task.temps_passe_sec = (task.temps_passe_sec or 0) + secondes
    db.session.commit()
    total = task.temps_passe_sec
    heures = total // 3600
    minutes = (total % 3600) // 60
    return jsonify({
        "success": True,
        "temps_passe_sec": total,
        "temps_formate": f"{heures}h {minutes:02d}min"
    })


# ---------- GET endpoints ----------

@bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    # Interventions du jour
    interventions_today = Intervention.query.filter(
        Intervention.date_creation >= today_start,
        Intervention.date_creation <= today_end
    ).all()

    # Tâches en cours
    tasks_in_progress = Task.query.filter_by(statut='in_progress').all()

    # Chrono actif
    active_timer = Task.query.filter_by(timer_running=True).first()

    # Pointage du jour
    pointage = Pointage.query.filter(
        Pointage.date >= today_start,
        Pointage.date <= today_end
    ).first()

    return jsonify({
        "date": today.strftime("%A %d %B %Y"),
        "interventions_today": [{
            "id": i.id, "titre": i.titre, "statut": i.statut,
            "priorite": i.priorite, "demandeur": i.demandeur
        } for i in interventions_today],
        "interventions_today_count": len(interventions_today),
        "tasks_in_progress": [{
            "id": t.id, "titre": t.titre, "priorite": t.priorite,
            "temps_passe_sec": t.temps_passe_sec or 0
        } for t in tasks_in_progress],
        "tasks_in_progress_count": len(tasks_in_progress),
        "active_timer": {
            "task_id": active_timer.id,
            "titre": active_timer.titre,
            "temps_passe_sec": active_timer.temps_passe_sec or 0
        } if active_timer else None,
        "pointage": {
            "arrivee": pointage.heure_arrivee.strftime("%H:%M") if pointage and pointage.heure_arrivee else None,
            "depart": pointage.heure_depart.strftime("%H:%M") if pointage and pointage.heure_depart else None,
        } if pointage else None
    })
