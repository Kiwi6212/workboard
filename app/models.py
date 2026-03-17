from datetime import datetime, timezone, date, time

from app import db


class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    date_debut = db.Column(db.DateTime, nullable=False)
    date_fin = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(20), nullable=False, default="tache")  # cours, tache, perso, alternance
    couleur = db.Column(db.String(7), default="#3b82f6")


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    statut = db.Column(db.String(20), nullable=False, default="todo")  # todo, in_progress, done
    priorite = db.Column(db.Integer, default=0)
    temps_passe_sec = db.Column(db.Integer, default=0)
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Document(db.Model):
    __tablename__ = "documents"
    id = db.Column(db.Integer, primary_key=True)
    nom_original = db.Column(db.String(255), nullable=False)
    chemin = db.Column(db.String(255), nullable=False)
    categorie = db.Column(db.String(20), default="autre")  # bulletin, contrat, cours, autre
    date_ajout = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    taille = db.Column(db.Integer, default=0)


class Note(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    contenu_md = db.Column(db.Text, default="")
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_modif = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Intervention(db.Model):
    __tablename__ = "interventions"
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    lieu = db.Column(db.String(200), default="")
    demandeur = db.Column(db.String(200), default="")
    type_probleme = db.Column(db.String(20), nullable=False, default="autre")  # reseau, materiel, logiciel, imprimante, autre
    priorite = db.Column(db.String(10), nullable=False, default="normal")  # urgent, normal
    type_intervention = db.Column(db.String(20), nullable=False, default="intervention")  # intervention, mission
    statut = db.Column(db.String(20), nullable=False, default="en_attente")  # en_attente, en_cours, resolu, non_resolu
    duree_minutes = db.Column(db.Integer, nullable=True)
    notes_solution = db.Column(db.Text, nullable=True)
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_resolution = db.Column(db.DateTime, nullable=True)


class Pointage(db.Model):
    __tablename__ = "pointages"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True, default=lambda: date.today())
    heure_arrivee = db.Column(db.Time, nullable=False)
    heure_depart = db.Column(db.Time, nullable=True)
    pause_minutes = db.Column(db.Integer, default=60)
    heures_travaillees = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def calculer_heures(self):
        if self.heure_arrivee and self.heure_depart:
            arrivee_min = self.heure_arrivee.hour * 60 + self.heure_arrivee.minute
            depart_min = self.heure_depart.hour * 60 + self.heure_depart.minute
            travail_min = depart_min - arrivee_min - (self.pause_minutes or 0)
            self.heures_travaillees = round(max(travail_min, 0) / 60, 2)


class HeureSup(db.Model):
    __tablename__ = "heures_sup"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    duree_minutes = db.Column(db.Integer, nullable=False)
    motif = db.Column(db.Text, nullable=True)
    validee = db.Column(db.Boolean, default=False)


class Goal(db.Model):
    __tablename__ = "goals"
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    valeur_cible = db.Column(db.Float, nullable=False, default=100)
    valeur_actuelle = db.Column(db.Float, default=0)
    unite = db.Column(db.String(50), default="%")
    date_echeance = db.Column(db.DateTime, nullable=True)
    couleur = db.Column(db.String(7), default="#10b981")
