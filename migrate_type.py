"""Migration: add type_intervention column to interventions table + create pointages/heures_sup tables."""
import sqlite3

DB_PATH = "workboard.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add type_intervention column if it doesn't exist
try:
    cursor.execute("ALTER TABLE interventions ADD COLUMN type_intervention VARCHAR(20) DEFAULT 'intervention'")
    print("Added type_intervention column to interventions table.")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("type_intervention column already exists.")
    else:
        raise

# Create pointages table
cursor.execute("""
CREATE TABLE IF NOT EXISTS pointages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    heure_arrivee TIME NOT NULL,
    heure_depart TIME,
    pause_minutes INTEGER DEFAULT 60,
    heures_travaillees FLOAT,
    notes TEXT
)
""")
print("pointages table ready.")

# Create heures_sup table
cursor.execute("""
CREATE TABLE IF NOT EXISTS heures_sup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    duree_minutes INTEGER NOT NULL,
    motif TEXT,
    validee BOOLEAN DEFAULT 0
)
""")
print("heures_sup table ready.")

conn.commit()
conn.close()
print("Migration complete.")
