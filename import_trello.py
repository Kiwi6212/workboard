import json
import re
import sys
from datetime import datetime, timezone

from app import create_app, db
from app.models import Intervention

sys.stdout.reconfigure(encoding="utf-8")

app = create_app()

with open("trello_export.json", encoding="utf-8") as f:
    data = json.load(f)

# Build mappings
list_map = {l["id"]: l for l in data.get("lists", [])}
closed_list_ids = {l["id"] for l in data.get("lists", []) if l.get("closed")}

# Build card_id → comments mapping (latest comment per card)
card_comments = {}
for action in data.get("actions", []):
    if action.get("type") == "commentCard":
        card_id = action["data"]["card"]["id"]
        if card_id not in card_comments:
            card_comments[card_id] = action["data"]["text"]


def get_statut(list_id):
    name = list_map.get(list_id, {}).get("name", "").lower()
    if "faire" in name:
        return "en_attente"
    if "cours" in name:
        return "en_cours"
    if "ermin" in name:
        return "resolu"
    return None


def get_type_probleme(labels):
    for label in labels:
        name = label.get("name", "").lower()
        if name in ("antivirus", "chocolatey") or "canope" in name:
            return "logiciel"
        if "réseau" in name or "reseau" in name:
            return "reseau"
    return "autre"


def parse_comment(text):
    """Extract date, duration, and notes from comment text."""
    parsed_date = None
    duree_minutes = None
    lines = text.strip().split("\n")
    remaining_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Try date extraction
        date_match = re.search(r"[Ff]ait\s+le?\s*(\d{2}/\d{2}/\d{4})", stripped)
        if date_match and parsed_date is None:
            try:
                parsed_date = datetime.strptime(date_match.group(1), "%d/%m/%Y").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
            continue

        # Try duration: Xh or XhY or X min
        dur_h_match = re.match(r"^(\d+)\s*h\s*(\d+)?\s*$", stripped, re.I)
        dur_m_match = re.match(r"^(\d+)\s*min\s*$", stripped, re.I)
        if dur_h_match and duree_minutes is None:
            hours = int(dur_h_match.group(1))
            mins = int(dur_h_match.group(2)) if dur_h_match.group(2) else 0
            duree_minutes = hours * 60 + mins
            continue
        if dur_m_match and duree_minutes is None:
            duree_minutes = int(dur_m_match.group(1))
            continue

        remaining_lines.append(stripped)

    notes = "\n".join(remaining_lines).strip() or None
    return parsed_date, duree_minutes, notes


stats = {"total": 0, "with_date": 0, "with_duration": 0}
first_five = []

with app.app_context():
    for card in data.get("cards", []):
        if card.get("closed"):
            continue
        list_id = card.get("idList", "")
        if list_id in closed_list_ids:
            continue
        statut = get_statut(list_id)
        if statut is None:
            continue

        # Parse comment if available
        comment_text = card_comments.get(card["id"], "")
        parsed_date, duree_minutes, notes_solution = parse_comment(comment_text) if comment_text else (None, None, None)

        # Fallback date
        if parsed_date:
            date_creation = parsed_date
            stats["with_date"] += 1
        elif card.get("dateLastActivity"):
            try:
                date_creation = datetime.fromisoformat(card["dateLastActivity"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                date_creation = datetime.now(timezone.utc)
        else:
            date_creation = datetime.now(timezone.utc)

        if duree_minutes is not None:
            stats["with_duration"] += 1

        # Date resolution for resolved
        date_resolution = date_creation if statut == "resolu" else None

        intervention = Intervention(
            titre=card.get("name", "").strip(),
            lieu="",
            demandeur="",
            type_probleme=get_type_probleme(card.get("labels", [])),
            priorite="normal",
            statut=statut,
            duree_minutes=duree_minutes,
            notes_solution=notes_solution,
            date_creation=date_creation,
            date_resolution=date_resolution,
        )
        db.session.add(intervention)
        stats["total"] += 1

        if len(first_five) < 5:
            first_five.append({
                "titre": intervention.titre,
                "statut": intervention.statut,
                "type_probleme": intervention.type_probleme,
                "date_creation": str(date_creation),
                "duree_minutes": duree_minutes,
                "notes_solution": notes_solution,
            })

    db.session.commit()

print(f"Imported {stats['total']} interventions")
print(f"  - {stats['with_date']} had a parsed date from comment")
print(f"  - {stats['with_duration']} had a parsed duration from comment")
print()
print("First 5 imported interventions:")
for i, item in enumerate(first_five, 1):
    print(f"\n  [{i}] {item['titre']}")
    print(f"      statut: {item['statut']} | type: {item['type_probleme']}")
    print(f"      date: {item['date_creation']}")
    print(f"      durée: {item['duree_minutes']} min")
    print(f"      notes: {item['notes_solution']}")
