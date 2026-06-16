# SPEC — Système de contrôle de présence par QR code

## Objectif

Application web Flask permettant à des enseignants de faire l'appel via des QR codes permanents imprimés sur une feuille par groupe d'étudiants. Les étudiants flashent leur QR code personnel ; l'enseignant voit les présences s'afficher en temps réel sur son smartphone.

---

## Stack technique

- **Backend** : Python 3.x, Flask, SQLite (via `sqlite3` stdlib)
- **QR codes** : bibliothèque `qrcode[pil]`
- **Hébergement** : Render (free tier), déploiement via GitHub
- **Frontend** : HTML/CSS vanilla, pas de framework JS — juste un `<meta refresh>` toutes les 5 secondes sur la page admin pour simuler le temps réel

---

## Structure du projet

```
presence/
├── app.py
├── init_db.py
├── generate_qr.py
├── data/
│   └── etudiants_5A.csv
├── templates/
│   ├── admin.html
│   ├── nouvelle_session.html
│   └── scan.html
├── static/
│   └── style.css
├── requirements.txt
└── render.yaml
```

---

## Base de données : `presence.db`

### Table `etudiants`
```sql
CREATE TABLE etudiants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    groupe TEXT NOT NULL
);
```

### Table `sessions`
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    groupe TEXT NOT NULL,
    cours TEXT NOT NULL,
    date_heure TEXT NOT NULL  -- ISO format, ex: "2026-06-16 10:30"
);
```

### Table `presences`
```sql
CREATE TABLE presences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    etudiant_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    UNIQUE(etudiant_id, session_id),  -- un seul scan par session
    FOREIGN KEY (etudiant_id) REFERENCES etudiants(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

---

## Routes Flask

### `GET /scan/<etudiant_id>`
- Vérifie que `etudiant_id` existe
- Vérifie qu'une session est active (= la session ouverte la plus récente, toutes sessions confondues, de moins de 4 heures)
- Si l'étudiant a déjà scanné pour cette session : ne rien faire (pas d'erreur, pas de double enregistrement)
- Sinon : enregistre la présence avec timestamp
- Dans tous les cas : affiche `scan.html` avec le nom et prénom de l'étudiant et le message "Présence enregistrée" ou "Déjà enregistré"

### `GET /admin`
- Affiche le formulaire de mot de passe si non authentifié
- Si authentifié : affiche la session active en cours (si elle existe) avec la liste des présents et le compteur, plus un lien "Nouvelle session"
- Rafraîchissement automatique toutes les 5 secondes via `<meta http-equiv="refresh" content="5">`

### `POST /admin/login`
- Vérifie le mot de passe (variable d'environnement `ADMIN_PASSWORD`)
- Utilise une session Flask (`session['auth'] = True`)

### `GET /admin/logout`
- Déconnecte

### `POST /admin/session/nouvelle`
- Crée une nouvelle session avec le groupe et le cours soumis via formulaire
- Redirige vers `/admin`

### `GET /admin/session/<session_id>`
- Vue détaillée d'une session passée : liste des présents avec timestamps
- Accessible uniquement si authentifié

### `GET /admin/historique`
- Liste de toutes les sessions passées (groupe, cours, date, nombre de présents)
- Lien vers chaque session détaillée

---

## Logique "session active"

Une session est considérée **active** si elle est la plus récente **et** qu'elle a été créée il y a moins de 4 heures. Un seul enseignant peut donc avoir une session ouverte à la fois (simplifié volontairement). Si plusieurs enseignants utilisent l'app simultanément, les scans vont tous dans la même session active — c'est acceptable pour l'usage prévu.

---

## Script `init_db.py`

- Crée `presence.db` si elle n'existe pas
- Crée les trois tables
- Importe `data/etudiants_5A.csv` dans la table `etudiants`
- Idempotent : ne recrée pas les étudiants s'ils existent déjà (vérification sur nom+prenom+groupe)

---

## Script `generate_qr.py`

- Lit `data/etudiants_5A.csv`
- Pour chaque étudiant, génère un QR code pointant vers `https://<BASE_URL>/scan/<etudiant_id>`
- `BASE_URL` est lu depuis une variable d'environnement ou passé en argument CLI
- Produit un PDF imprimable : grille de QR codes avec nom+prénom sous chaque code, ~6 par ligne
- Format A4, adapté à une impression lisible par smartphone standard
- Sortie : `qrcodes_5A.pdf`

**Note** : `generate_qr.py` tourne en **local** (pas sur Render). L'enseignant le lance une seule fois après déploiement pour générer le PDF à imprimer.

---

## Données initiales

Le fichier `data/etudiants_5A.csv` contient 47 étudiants du groupe 5A (promo GMM INSA Toulouse). Format :

```
nom,prenom,groupe
ADDI,RAPHAEL,5A
AOUBAIDA,AYMAN,5A
...
```

Les IDs en base seront 1 à 47 dans l'ordre d'insertion.

---

## Cours disponibles (menu déroulant)

Pour l'instant, liste en dur dans le formulaire "Nouvelle session" :
- Image
- Optimisation
- Signal
- Ondelettes
- Projet
- Autre

---

## Sécurité

- Mot de passe admin unique, stocké dans la variable d'environnement `ADMIN_PASSWORD`
- Clé secrète Flask dans la variable d'environnement `SECRET_KEY`
- Pas d'authentification côté scan (les URLs `/scan/<id>` sont publiques — c'est voulu)
- Pas de HTTPS à gérer (Render le fournit automatiquement)

---

## Configuration Render (`render.yaml`)

```yaml
services:
  - type: web
    name: presence-insa
    env: python
    buildCommand: "pip install -r requirements.txt && python init_db.py"
    startCommand: "gunicorn app:app"
    envVars:
      - key: ADMIN_PASSWORD
        sync: false
      - key: SECRET_KEY
        sync: false
```

**Important** : sur Render free tier, le filesystem est éphémère. La base SQLite est donc réinitialisée à chaque redéploiement. Pour un usage en production à l'INSA, il faudra soit utiliser un disque persistant Render (payant), soit migrer vers PostgreSQL. Pour les tests, ce n'est pas un problème.

---

## `requirements.txt`

```
flask
qrcode[pil]
gunicorn
pillow
reportlab
```

---

## Interface admin — comportement attendu

### Page principale `/admin` (authentifié)

- En-tête : "Contrôle de présence — GMM INSA Toulouse"
- Si session active : affiche "Session en cours : [cours] — Groupe [groupe] — [date heure]"
- Compteur en gros : "X présents"
- Liste des présents : Nom Prénom, heure du scan
- Bouton "Nouvelle session"
- Lien "Historique"
- Design minimaliste, lisible sur smartphone (pas besoin d'être beau)

### Page scan `/scan/<id>`

- Grande police, centré
- "Bonjour [Prénom] [Nom]" 
- "✓ Présence enregistrée" ou "ℹ️ Déjà enregistré"
- Pas de lien, pas de navigation — juste la confirmation

---

## Ce qui est hors scope (pour l'instant)

- Export CSV des présences
- Notifications
- Gestion multi-groupes simultanée
- Authentification par enseignant
- Interface d'ajout d'étudiants en ligne
