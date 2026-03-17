"""Reclassify interventions by keyword rules (no external API)."""
import json
import sqlite3

DB_PATH = "workboard.db"
TRELLO_PATH = "trello_export.json"

MISSION_KEYWORDS = [
    "installation", "installer", "vérif", "verification",
    "cablage", "câblage", "réseau complet",
    "bcdi", "sidoc", "bitdefender", "chocolatey", "canope",
    "domaine", "déploiement", "migration", "mise en place",
    "infrastructure", "serveur", "configuration", "setup",
    "projet", "sw complet",
]

INTERVENTION_KEYWORDS = [
    "primaire", "lycee", "lycée", "college", "collège",
    "salle", "cdi", "ordi", "pc", "prblm", "problème",
    "tbi", "imp", "scan", "restart", "déconne",
    "panne", "réparer", "dépannage", "écran", "clavier",
    "souris", "imprimante", "wifi", "branchement",
]


def text_contains(text, keywords):
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def main():
    # Load Trello label mapping
    with open(TRELLO_PATH, "r", encoding="utf-8") as f:
        trello = json.load(f)

    trello_mission_titles = set()
    for card in trello.get("cards", []):
        labels = card.get("labels", [])
        if any(l.get("name", "").strip() for l in labels):
            trello_mission_titles.add(card.get("name", "").strip())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, titre, notes_solution, type_intervention FROM interventions")
    rows = cursor.fetchall()

    deleted = 0
    missions = 0
    interventions = 0

    for row_id, titre, notes, current_type in rows:
        titre = titre or ""
        notes = notes or ""

        # Rule 1 — Delete separators
        if "---" in titre:
            cursor.execute("DELETE FROM interventions WHERE id = ?", (row_id,))
            deleted += 1
            continue

        # Rule 2 — Mission keywords
        if text_contains(titre, MISSION_KEYWORDS) or text_contains(notes, MISSION_KEYWORDS):
            cursor.execute(
                "UPDATE interventions SET type_intervention = 'mission' WHERE id = ?",
                (row_id,),
            )
            missions += 1
            continue

        # Rule 3 — Mission by Trello label
        if titre.strip() in trello_mission_titles:
            cursor.execute(
                "UPDATE interventions SET type_intervention = 'mission' WHERE id = ?",
                (row_id,),
            )
            missions += 1
            continue

        # Rule 4 — Intervention keywords
        if text_contains(titre, INTERVENTION_KEYWORDS):
            cursor.execute(
                "UPDATE interventions SET type_intervention = 'intervention' WHERE id = ?",
                (row_id,),
            )
            interventions += 1
            continue

        # Rule 5 — Default: stays intervention
        interventions += 1

    conn.commit()
    conn.close()

    print(f"Deleted: {deleted} | Missions: {missions} | Interventions: {interventions}")


if __name__ == "__main__":
    main()
