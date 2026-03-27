from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app import db, csrf
from app.models import Note, Intervention, Task, Pointage, Document, HeureSup, Goal, Event

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


# ---------- GET list endpoints ----------

@bp.route('/tasks', methods=['GET'])
def get_tasks():
    statut = request.args.get('statut')
    query = Task.query.order_by(Task.priorite.desc(), Task.date_creation.desc())
    if statut:
        query = query.filter_by(statut=statut)
    tasks = query.limit(50).all()
    return jsonify([{
        "id": t.id,
        "titre": t.titre,
        "description": t.description,
        "statut": t.statut,
        "priorite": t.priorite,
        "temps_passe_sec": t.temps_passe_sec or 0,
        "timer_running": t.timer_running,
        "date_creation": t.date_creation.isoformat() if t.date_creation else None,
    } for t in tasks])


@bp.route('/interventions', methods=['GET'])
def get_interventions():
    statut = request.args.get('statut')
    priorite = request.args.get('priorite')
    query = Intervention.query.order_by(Intervention.date_creation.desc())
    if statut:
        query = query.filter_by(statut=statut)
    if priorite:
        query = query.filter_by(priorite=priorite)
    interventions = query.limit(50).all()
    return jsonify([{
        "id": i.id,
        "titre": i.titre,
        "lieu": i.lieu,
        "demandeur": i.demandeur,
        "type_probleme": i.type_probleme,
        "priorite": i.priorite,
        "type_intervention": i.type_intervention,
        "statut": i.statut,
        "duree_minutes": i.duree_minutes,
        "notes_solution": i.notes_solution,
        "date_creation": i.date_creation.isoformat() if i.date_creation else None,
        "date_resolution": i.date_resolution.isoformat() if i.date_resolution else None,
    } for i in interventions])


@bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.order_by(Note.date_modif.desc()).all()
    return jsonify([{
        "id": n.id,
        "titre": n.titre,
        "contenu_md": n.contenu_md,
        "date_creation": n.date_creation.isoformat() if n.date_creation else None,
        "date_modif": n.date_modif.isoformat() if n.date_modif else None,
    } for n in notes])


@bp.route('/documents', methods=['GET'])
def get_documents():
    docs = Document.query.order_by(Document.date_ajout.desc()).all()
    return jsonify([{
        "id": d.id,
        "nom_original": d.nom_original,
        "categorie": d.categorie,
        "date_ajout": d.date_ajout.isoformat() if d.date_ajout else None,
        "taille": d.taille,
    } for d in docs])


@bp.route('/heures-sup', methods=['GET'])
def get_heures_sup():
    hs = HeureSup.query.order_by(HeureSup.date.desc()).all()
    return jsonify([{
        "id": h.id,
        "date": h.date.isoformat() if h.date else None,
        "duree_minutes": h.duree_minutes,
        "motif": h.motif,
        "validee": h.validee,
    } for h in hs])


@bp.route('/pointage/historique', methods=['GET'])
def get_pointage_historique():
    pointages = Pointage.query.order_by(Pointage.date.desc()).limit(30).all()
    return jsonify([{
        "id": p.id,
        "date": p.date.isoformat() if p.date else None,
        "heure_arrivee": p.heure_arrivee.strftime("%H:%M") if p.heure_arrivee else None,
        "heure_depart": p.heure_depart.strftime("%H:%M") if p.heure_depart else None,
        "pause_minutes": p.pause_minutes,
        "heures_travaillees": p.heures_travaillees,
        "notes": p.notes,
    } for p in pointages])


@bp.route('/stats/interventions', methods=['GET'])
def get_stats_interventions():
    total = Intervention.query.count()
    en_attente = Intervention.query.filter_by(statut="en_attente").count()
    en_cours = Intervention.query.filter_by(statut="en_cours").count()
    resolues = Intervention.query.filter_by(statut="resolu").count()
    non_resolues = Intervention.query.filter_by(statut="non_resolu").count()
    urgentes = Intervention.query.filter_by(priorite="urgent").count()
    avg_duree = db.session.query(func.avg(Intervention.duree_minutes)).filter(
        Intervention.duree_minutes.isnot(None)
    ).scalar() or 0
    return jsonify({
        "total": total,
        "en_attente": en_attente,
        "en_cours": en_cours,
        "resolues": resolues,
        "non_resolues": non_resolues,
        "urgentes": urgentes,
        "duree_moyenne_minutes": round(avg_duree, 1),
    })


@bp.route('/stats/tasks', methods=['GET'])
def get_stats_tasks():
    total = Task.query.count()
    todo = Task.query.filter_by(statut="todo").count()
    in_progress = Task.query.filter_by(statut="in_progress").count()
    done = Task.query.filter_by(statut="done").count()
    total_temps = db.session.query(func.sum(Task.temps_passe_sec)).scalar() or 0
    return jsonify({
        "total": total,
        "todo": todo,
        "in_progress": in_progress,
        "done": done,
        "temps_total_sec": total_temps,
    })


@bp.route('/stats/pointage', methods=['GET'])
def get_stats_pointage():
    today = date.today()
    pointage_today = Pointage.query.filter_by(date=today).first()
    total_days = Pointage.query.count()
    avg_hours = db.session.query(func.avg(Pointage.heures_travaillees)).filter(
        Pointage.heures_travaillees.isnot(None)
    ).scalar() or 0
    return jsonify({
        "today": {
            "arrivee": pointage_today.heure_arrivee.strftime("%H:%M") if pointage_today and pointage_today.heure_arrivee else None,
            "depart": pointage_today.heure_depart.strftime("%H:%M") if pointage_today and pointage_today.heure_depart else None,
            "heures_travaillees": pointage_today.heures_travaillees if pointage_today else None,
        },
        "total_jours": total_days,
        "moyenne_heures": round(avg_hours, 2),
    })


@bp.route('/planning', methods=['GET'])
def get_planning():
    scope = request.args.get('scope', 'upcoming')
    now = datetime.now(timezone.utc)
    query = Event.query
    if scope == 'upcoming':
        query = query.filter(Event.date_debut >= now)
    elif scope == 'past':
        query = query.filter(Event.date_debut < now)
    events = query.order_by(Event.date_debut).all()
    return jsonify([{
        "id": e.id,
        "titre": e.titre,
        "description": e.description,
        "type": e.type,
        "date_debut": e.date_debut.isoformat() if e.date_debut else None,
        "date_fin": e.date_fin.isoformat() if e.date_fin else None,
    } for e in events])


# ---------- POST action endpoints (status, timer, edit) ----------

@bp.route('/tasks/<int:task_id>/statut', methods=['POST'])
@csrf.exempt
def change_task_statut(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json() or request.form
    new_statut = data.get('statut')
    if new_statut in ['todo', 'in_progress', 'done']:
        task.statut = new_statut
        db.session.commit()
        return jsonify({"success": True, "statut": task.statut})
    return jsonify({"success": False, "error": "Statut invalide"}), 400


@bp.route('/tasks/<int:task_id>/timer', methods=['POST'])
@csrf.exempt
def control_task_timer(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json() or request.form
    action = data.get('action')
    now = datetime.now()
    if action == 'start':
        task.timer_running = True
        task.timer_start = now
    elif action == 'stop':
        if task.timer_running and task.timer_start:
            elapsed = (now - task.timer_start.replace(tzinfo=None)).total_seconds()
            task.temps_passe_sec = (task.temps_passe_sec or 0) + int(elapsed)
        task.timer_running = False
        task.timer_start = None
    elif action == 'reset':
        task.timer_running = False
        task.timer_start = None
        task.temps_passe_sec = 0
    else:
        return jsonify({"success": False, "error": "Action invalide"}), 400
    db.session.commit()
    return jsonify({"success": True, "timer_running": task.timer_running, "temps_passe_sec": task.temps_passe_sec or 0})


@bp.route('/interventions/<int:intervention_id>/statut', methods=['PUT', 'POST'])
@csrf.exempt
def change_intervention_statut(intervention_id):
    intervention = Intervention.query.get_or_404(intervention_id)
    data = request.get_json() or request.form
    new_statut = data.get('statut')
    if new_statut in ['en_attente', 'en_cours', 'resolu', 'non_resolu']:
        intervention.statut = new_statut
        if new_statut == 'resolu':
            intervention.date_resolution = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({"success": True, "statut": intervention.statut})
    return jsonify({"success": False, "error": "Statut invalide"}), 400


@bp.route('/interventions/<int:intervention_id>', methods=['PUT'])
@csrf.exempt
def update_intervention(intervention_id):
    intervention = Intervention.query.get_or_404(intervention_id)
    data = request.get_json()
    if 'titre' in data:
        intervention.titre = data['titre']
    if 'lieu' in data:
        intervention.lieu = data['lieu']
    if 'demandeur' in data:
        intervention.demandeur = data['demandeur']
    if 'type_probleme' in data:
        intervention.type_probleme = data['type_probleme']
    if 'priorite' in data:
        intervention.priorite = data['priorite']
    if 'statut' in data:
        intervention.statut = data['statut']
    if 'notes_solution' in data:
        intervention.notes_solution = data['notes_solution']
    if 'duree_minutes' in data:
        intervention.duree_minutes = data['duree_minutes']
    db.session.commit()
    return jsonify({"success": True, "intervention": {
        "id": intervention.id, "titre": intervention.titre,
        "statut": intervention.statut, "priorite": intervention.priorite
    }})


@bp.route('/notes/<int:note_id>', methods=['PUT'])
@csrf.exempt
def update_note(note_id):
    note = Note.query.get_or_404(note_id)
    data = request.get_json()
    if 'titre' in data:
        note.titre = data['titre']
    if 'contenu_md' in data:
        note.contenu_md = data['contenu_md']
    db.session.commit()
    return jsonify({"success": True, "note": {
        "id": note.id, "titre": note.titre,
        "contenu_md": note.contenu_md
    }})


@bp.route('/goals/<int:goal_id>/update', methods=['POST'])
@csrf.exempt
def api_update_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    data = request.get_json() or request.form
    if 'valeur_actuelle' in data:
        goal.valeur_actuelle = float(data['valeur_actuelle'])
    db.session.commit()
    return jsonify({"success": True, "valeur_actuelle": goal.valeur_actuelle})


@bp.route('/planning/<int:event_id>/delete', methods=['POST'])
@csrf.exempt
def api_delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({"success": True, "message": "vnement supprim"})


@bp.route('/stats/goals', methods=['GET'])
def get_stats_goals():
    goals = Goal.query.all()
    result = []
    for g in goals:
        pct = round(g.valeur_actuelle / g.valeur_cible * 100) if g.valeur_cible else 0
        result.append({
            "id": g.id,
            "titre": g.titre,
            "valeur_actuelle": g.valeur_actuelle,
            "valeur_cible": g.valeur_cible,
            "unite": g.unite,
            "pourcentage": min(pct, 100),
        })
    return jsonify(result)
