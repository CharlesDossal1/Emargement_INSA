import sqlite3
import csv
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "presence.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "etudiants_5A.csv")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS etudiants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            groupe TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            groupe TEXT NOT NULL,
            cours TEXT NOT NULL,
            date_heure TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS presences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            etudiant_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            UNIQUE(etudiant_id, session_id),
            FOREIGN KEY (etudiant_id) REFERENCES etudiants(id),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
    """)

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                "SELECT id FROM etudiants WHERE nom=? AND prenom=? AND groupe=?",
                (row["nom"], row["prenom"], row["groupe"]),
            )
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO etudiants (nom, prenom, groupe) VALUES (?, ?, ?)",
                    (row["nom"], row["prenom"], row["groupe"]),
                )

    conn.commit()
    conn.close()
    print("Base de données initialisée.")


if __name__ == "__main__":
    init_db()
