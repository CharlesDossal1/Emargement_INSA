# CLAUDE.md — Conventions du projet `presence`

## Contexte

Projet Flask minimal de contrôle de présence par QR code pour des enseignants de l'INSA Toulouse. L'objectif est la **simplicité** : pas de sur-ingénierie, pas de dépendances inutiles.

## Règles générales

- Ne pas introduire de dépendances non listées dans `requirements.txt` sans en discuter
- Pas de JavaScript frameworks (React, Vue, etc.) — HTML vanilla uniquement
- Pas d'ORM (SQLAlchemy, etc.) — `sqlite3` stdlib uniquement
- Garder les fichiers courts et lisibles

## Ordre de réalisation suggéré

1. `requirements.txt`
2. `data/etudiants_5A.csv` (déjà fourni)
3. `init_db.py`
4. `app.py` (routes dans l'ordre : scan, admin, login, logout, nouvelle session, historique)
5. `templates/scan.html`
6. `templates/admin.html`
7. `templates/nouvelle_session.html`
8. `static/style.css`
9. `generate_qr.py`
10. `render.yaml`

## Conventions de code

- Python : snake_case, fonctions courtes
- Templates : Jinja2 standard, pas de logique complexe dans les templates
- CSS : minimaliste, mobile-first (l'admin est utilisée sur smartphone)
- Commentaires en français

## Variables d'environnement requises

- `ADMIN_PASSWORD` : mot de passe admin (obligatoire en prod)
- `SECRET_KEY` : clé secrète Flask (obligatoire en prod)
- `BASE_URL` : URL de base pour générer les QR codes (ex: `https://presence-insa.onrender.com`), utilisé uniquement par `generate_qr.py` en local

## Points d'attention

- `init_db.py` doit être idempotent (Render le lance à chaque déploiement)
- La session active est déterminée par la plus récente session créée il y a moins de 4 heures
- Un double scan doit être silencieusement ignoré (contrainte UNIQUE en base suffit, attraper l'IntegrityError)
- `generate_qr.py` tourne en local uniquement, pas besoin qu'il fonctionne sur Render

## Test en local

```bash
pip install -r requirements.txt
python init_db.py
ADMIN_PASSWORD=test SECRET_KEY=dev flask run
```

Puis pour générer les QR codes :
```bash
BASE_URL=http://localhost:5000 python generate_qr.py
```
