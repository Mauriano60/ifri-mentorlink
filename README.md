# IFRI_MentorLink

Plateforme de mise en relation entre étudiants pour le mentorat académique. Les étudiants peuvent publier des offres (proposer leur aide) ou des demandes (chercher de l'aide) et être matchés automatiquement selon leurs compétences, disponibilités et affinités.

---

## Technologies

### Backend
- **Python 3.13** — langage serveur
- **Flask** — framework web
- **PyMySQL** — connecteur MySQL
- **Werkzeug** — hash des mots de passe, sécurisation des uploads
- **Flask-Mail** — envoi d'emails (vérification, mot de passe oublié)
- **Flask-Limiter** — rate limiting
- **python-dotenv** — variables d'environnement
- **pytest** — tests unitaires

### Base de données
- **MySQL 8.0** — base de données relationnelle
- 15 tables : utilisateurs, matières, filières, niveaux, offres, demandes, correspondances, disponibilités, notifications, conversations, messages, compétences, difficultés, etc.

### Frontend
- **HTML5 / Jinja2** — templates rendus côté serveur
- **Bootstrap 5.3** + **Bootstrap Icons** — UI
- **CSS personnalisé** — thème bleu `#2563EB` / slate `#0F172A` / teal `#14B8A6`
- **JavaScript vanilla** — filtres, disponibilités dynamiques, upload avatar

---

## Architecture du backend

```
backend/
├── app.py                  # Point d'entrée Flask
├── config/settings.py      # Configuration (DB, mail, uploads)
├── db/database.py          # Connexion MySQL (fetch_one, fetch_all, execute)
├── routes/                 # Blueprints Flask
│   ├── auth.py             # Inscription, connexion, déconnexion
│   ├── users.py            # Dashboard, profil public
│   ├── offres.py           # Catalogue + création d'offres de mentorat
│   ├── demandes.py         # Catalogue + création de demandes d'aide
│   ├── matching.py         # Page matching, envoi de demande
│   ├── notifications.py    # Liste et filtres des notifications
│   ├── conversations.py    # Messagerie privée
│   ├── parametres.py       # Profil, matières, confidentialité, préférences
│   ├── email.py            # Vérification email, mot de passe oublié
│   └── references.py       # Données de référence (matières, filières, etc.)
├── services/
│   ├── matching_service.py # Algorithme de scoring des correspondances
│   ├── notification_service.py  # Création de notifications
│   └── mail_service.py     # Envoi d'emails
├── templates/              # Templates Jinja2
│   ├── landing.html        # Page d'accueil publique
│   ├── auth/               # Login, register
│   ├── dashboard/          # Tableau de bord
│   ├── mentorat/           # Offres, demandes, création
│   ├── matching/           # Page matching
│   ├── notifications/      # Notifications
│   ├── conversations/      # Messagerie
│   ├── settings/           # Paramètres (4 onglets)
│   └── profil/             # Profil public
├── static/                 # CSS, JS, Bootstrap, uploads
└── utils/                  # Fonctions utilitaires (contexte utilisateur, validation)
```

### Principe de fonctionnement

- **Pas d'API REST** : le backend utilise exclusivement du rendu serveur avec Jinja2. Chaque route Flask renvoie une page HTML complète.
- **Connexion unique MySQL** : via `db/database.py` avec un pool implicite (ouverture/fermeture par requête). Trois fonctions : `fetch_one`, `fetch_all`, `execute`.
- **Sessions** : l'authentification est gérée par session Flask (pas de JWT côté client pour le rendu serveur).
- **Blueprints** : chaque module de fonctionnalité est un Blueprint Flask indépendant, monté dans `app.py`.

### Algorithme de matching

Le `matching_service.py` calcule un score de compatibilité sur 100 points entre deux étudiants :

| Critère | Poids | Détail |
|---|---|---|
| Annonces communes | 40 % | L'offre de l'un correspond à la demande de l'autre |
| Disponibilités | 30 % | Créneaux horaires compatibles |
| Filière | 20 % | Même filière = score max |
| Niveau d'étude | 10 % | Proximité de promotion |

Le résultat retourne pour chaque match : score, matières communes et disponibilités communes.

---

## Parcours utilisateur

### 1. Inscription et connexion
1. L'utilisateur s'inscrit avec email, mot de passe, prénom, nom, filière et niveau d'étude
2. Il reçoit un email de vérification (ou lien affiché en local)
3. Il se connecte et accède au **Dashboard**

### 2. Configuration du profil
1. Dans **Paramètres > Profil et matières** :
   - Ajoute ses matières de compétence (max 4)
   - Ajoute ses matières de difficulté (max 4)
   - Renseigne ses disponibilités (jour, heure début, heure fin)
   - Télécharge un avatar (PNG/JPG/WEBP, max 2 Mo)

### 3. Publication d'une annonce
- **Offre de mentorat** : « Je veux aider » → sélectionne une matière de compétence, un format (présentiel/visio), une description
- **Demande d'aide** : « J'ai besoin d'aide » → sélectionne une matière de difficulté, un format, une description
- Les disponibilités du profil sont automatiquement liées à l'annonce
- Après publication, un **matching instantané** suggère jusqu'à 5 étudiants compatibles

### 4. Matching dans le catalogue
1. L'utilisateur parcourt les offres/demandes disponibles
2. Il clique **« Faire le match »** sur une annonce → le système calcule la compatibilité et affiche le score, les matières communes et les disponibilités communes
3. Si le résultat lui convient, il clique **« Demander de l'aide »** (offre) ou **« Offrir mon aide »** (demande)
4. Une correspondance est créée et le destinataire reçoit une notification

### 5. Communication
1. Le destinataire voit la notification dans son tableau de bord
2. Il peut accepter ou refuser la demande
3. Une fois acceptée, les deux parties peuvent échanger via la **messagerie intégrée**

### 6. Notifications
- Trois filtres : Toutes, Match-demande, Infos
- Les notifications sont créées automatiquement lors des actions clés (matching, message, etc.)
