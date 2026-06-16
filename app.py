import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, session, redirect, url_for, render_template, g
from init_db import init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
DB_PATH = os.path.join(os.path.dirname(__file__), "presence.db")

init_db()
SESSION_DUREE_HEURES = 4


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def session_active():
    """Retourne la session active (moins de 4h) ou None."""
    db = get_db()
    limite = datetime.now() - timedelta(hours=SESSION_DUREE_HEURES)
    row = db.execute(
        "SELECT * FROM sessions WHERE date_heure >= ? ORDER BY date_heure DESC LIMIT 1",
        (limite.strftime("%Y-%m-%d %H:%M"),),
    ).fetchone()
    return row


# --- Scan ---

@app.route("/scan/<int:etudiant_id>")
def scan(etudiant_id):
    db = get_db()
    etudiant = db.execute(
        "SELECT * FROM etudiants WHERE id=?", (etudiant_id,)
    ).fetchone()

    if etudiant is None:
        return render_template("scan.html", erreur="Étudiant inconnu."), 404

    sess = session_active()
    if sess is None:
        return render_template(
            "scan.html",
            etudiant=etudiant,
            message="Aucune session active en ce moment.",
            deja=False,
        )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    deja = False
    try:
        db.execute(
            "INSERT INTO presences (etudiant_id, session_id, timestamp) VALUES (?, ?, ?)",
            (etudiant_id, sess["id"], timestamp),
        )
        db.commit()
    except sqlite3.IntegrityError:
        deja = True

    return render_template("scan.html", etudiant=etudiant, deja=deja)


# --- Admin ---

def admin_requis(f):
    """Décorateur : redirige vers login si non authentifié."""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("auth"):
            return redirect(url_for("admin"))
        return f(*args, **kwargs)

    return wrapper


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("auth"):
        return render_template("admin.html", login=True)

    db = get_db()
    sess = session_active()
    presences = []
    if sess:
        presences = db.execute(
            """SELECT e.nom, e.prenom, p.timestamp
               FROM presences p
               JOIN etudiants e ON e.id = p.etudiant_id
               WHERE p.session_id=?
               ORDER BY p.timestamp""",
            (sess["id"],),
        ).fetchall()

    return render_template("admin.html", login=False, sess=sess, presences=presences)


@app.route("/admin/login", methods=["POST"])
def admin_login():
    if request.form.get("password") == ADMIN_PASSWORD:
        session["auth"] = True
    return redirect(url_for("admin"))


@app.route("/admin/logout")
def admin_logout():
    session.pop("auth", None)
    return redirect(url_for("admin"))


@app.route("/admin/session/nouvelle", methods=["GET", "POST"])
@admin_requis
def nouvelle_session():
    if request.method == "POST":
        groupe = request.form.get("groupe", "").strip()
        cours = request.form.get("cours", "").strip()
        date_heure = datetime.now().strftime("%Y-%m-%d %H:%M")
        db = get_db()
        db.execute(
            "INSERT INTO sessions (groupe, cours, date_heure) VALUES (?, ?, ?)",
            (groupe, cours, date_heure),
        )
        db.commit()
        return redirect(url_for("admin"))

    return render_template("nouvelle_session.html")


@app.route("/admin/session/<int:session_id>")
@admin_requis
def detail_session(session_id):
    db = get_db()
    sess = db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    if sess is None:
        return "Session introuvable.", 404

    presences = db.execute(
        """SELECT e.nom, e.prenom, p.timestamp
           FROM presences p
           JOIN etudiants e ON e.id = p.etudiant_id
           WHERE p.session_id=?
           ORDER BY p.timestamp""",
        (session_id,),
    ).fetchall()

    return render_template("detail_session.html", sess=sess, presences=presences)


@app.route("/admin/historique")
@admin_requis
def historique():
    db = get_db()
    rows = db.execute(
        """SELECT s.id, s.groupe, s.cours, s.date_heure,
                  COUNT(p.id) AS nb_presents
           FROM sessions s
           LEFT JOIN presences p ON p.session_id = s.id
           GROUP BY s.id
           ORDER BY s.date_heure DESC"""
    ).fetchall()
    return render_template("historique.html", sessions=rows)


if __name__ == "__main__":
    app.run(debug=True)
