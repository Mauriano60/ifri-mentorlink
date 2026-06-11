from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, flash
from db.database import fetch_one, fetch_all, execute
from utils.validators import valider_inscription, valider_competences_et_lacunes
from utils.csrf import csrf_required
from extensions import limiter
from services.mail_service import envoyer_email_confirmation, verify_token
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('landing.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf_required
@limiter.limit("5 per minute")
def login():
    error = None
    if request.method == 'POST':
        identifiant = request.form['email']
        password = request.form['password']
        
        try:
            if '@' in identifiant:
                user = fetch_one("SELECT * FROM utilisateurs WHERE email = %s AND est_actif = 1", (identifiant,))
            else:
                user = fetch_one("SELECT * FROM utilisateurs WHERE telephone = %s AND est_actif = 1", (identifiant,))
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user['mot_de_passe'].encode('utf-8')):
                if not user['email_verifie']:
                    error = "Veuillez confirmer votre adresse email avant de vous connecter"
                else:
                    session['user_id'] = user['id']
                    session['prenom'] = user['prenom']
                    session['nom'] = user['nom']
                    return redirect(url_for('users.dashboard'))
            else:
                error = "Identifiant ou mot de passe incorrect"
        except Exception as e:
            error = f"Erreur lors de la connexion: {str(e)}"
            
    return render_template('auth/login.html', error=error)

@auth_bp.route('/register', methods=['GET', 'POST'])
@csrf_required
def register():
    error = None
    
    # Chargement dynamique des filières, niveaux et matières avec fetch_all
    try:
        filieres = fetch_all("SELECT * FROM filieres_etudes")
        niveaux = fetch_all("SELECT * FROM niveaux_etudes")
        matieres = fetch_all("SELECT * FROM matieres ORDER BY nom")
    except Exception as e:
        filieres = []
        niveaux = []
        matieres = []
        error = f"Erreur lors du chargement des données: {str(e)}"

    current_step = request.form.get('step', '1')

    form_data = {}
    if request.method == 'POST':
        form_data = {
            'nom': request.form.get('nom', ''),
            'prenom': request.form.get('prenom', ''),
            'email': request.form.get('email', ''),
            'telephone': request.form.get('telephone', ''),
            'id_filiere': request.form.get('id_filiere', ''),
            'id_niveau': request.form.get('id_niveau', ''),
            'competences': request.form.getlist('competences'),
            'lacunes': request.form.getlist('lacunes'),
            'dispo_jours': request.form.getlist('dispo_jour'),
            'dispo_debuts': request.form.getlist('dispo_debut'),
            'dispo_fins': request.form.getlist('dispo_fin'),
        }

    if request.method == 'POST':
        erreurs = valider_inscription(request.form)
        if erreurs:
            error = " | ".join(erreurs)
            champs_etape1 = ['prenom', 'nom', 'email', 'telephone', 'password']
            champs_etape2 = ['id_filiere', 'id_niveau']
            if any(not request.form.get(c) for c in champs_etape1):
                current_step = '1'
            elif any(not request.form.get(c) for c in champs_etape2):
                current_step = '2'
            else:
                # Tous les champs sont remplis mais validation de contenu échouée
                # (email invalide, téléphone invalide, mot de passe trop faible)
                # Toutes ces erreurs concernent l'étape 1
                current_step = '1'
        else:
            try:
                prenom = request.form['prenom']
                nom = request.form['nom']
                email = request.form['email']
                telephone = request.form['telephone']
                password = request.form['password']
                id_filiere = request.form['id_filiere']
                id_niveau = request.form['id_niveau']
                
                # Récupération des listes de matières
                competences = request.form.getlist('competences')
                lacunes = request.form.getlist('lacunes')
                
                # SÉCURITÉ CRUCIALE : Validation des contraintes métiers
                est_valide, message_erreur = valider_competences_et_lacunes(competences, lacunes)
                if not est_valide:
                    error = message_erreur
                    current_step = '2'
                    return render_template('auth/register.html', error=error, filieres=filieres, niveaux=niveaux, matieres=matieres, current_step=current_step, form_data=form_data)
                
                # Validation : au moins une disponibilité requise
                dispo_jours = request.form.getlist('dispo_jour')
                dispo_debuts = request.form.getlist('dispo_debut')
                dispo_fins = request.form.getlist('dispo_fin')
                dispo_valides = 0
                for i, jour in enumerate(dispo_jours):
                    if jour and i < len(dispo_debuts) and i < len(dispo_fins) and dispo_debuts[i] and dispo_fins[i]:
                        dispo_valides += 1
                if dispo_valides == 0:
                    error = "Veuillez ajouter au moins un créneau de disponibilité."
                    current_step = '3'
                    return render_template('auth/register.html', error=error, filieres=filieres, niveaux=niveaux, matieres=matieres, current_step=current_step, form_data=form_data)
                
                # Hachage sécurisé du mot de passe
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                # Vérifier si un compte inactif existe déjà avec cet email ou téléphone
                compte_inactif = fetch_one("""
                    SELECT id FROM utilisateurs
                    WHERE (email = %s OR telephone = %s) AND est_actif = 0
                """, (email, telephone))

                if compte_inactif:
                    execute("""
                        UPDATE utilisateurs SET
                            prenom=%s, nom=%s, mot_de_passe=%s, telephone=%s,
                            id_filiere=%s, id_niveau=%s, est_actif=1, email_verifie=0,
                            avatar_url=NULL, biographie=NULL
                        WHERE id=%s
                    """, (prenom, nom, hashed.decode('utf-8'), telephone, id_filiere, id_niveau, compte_inactif['id']))
                    user_id = compte_inactif['id']
                else:
                    # Insertion de l'utilisateur avec execute (renvoie directement le lastrowid)
                    user_id = execute("""
                        INSERT INTO utilisateurs (email, telephone, mot_de_passe, prenom, nom, id_filiere, id_niveau)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (email, telephone, hashed.decode('utf-8'), prenom, nom, id_filiere, id_niveau))
                
                if user_id:
                    # Nettoyage des anciennes données (utile si réactivation)
                    execute("DELETE FROM competences_utilisateur WHERE utilisateur_id = %s", (user_id,))
                    execute("DELETE FROM difficultes_utilisateur WHERE utilisateur_id = %s", (user_id,))
                    execute("DELETE FROM disponibilites WHERE utilisateur_id = %s", (user_id,))

                    # Insertion des compétences sélectionnées en BDD (Table d'association)
                    for comp_id in competences:
                        execute("""
                        INSERT INTO competences_utilisateur (utilisateur_id, matiere_id) 
                        VALUES (%s, %s)
                        """, (user_id, comp_id))
                        
                    # Insertion des lacunes sélectionnées en BDD (Table d'association)
                    for lacune_id in lacunes:
                        execute("""
                        INSERT INTO difficultes_utilisateur (utilisateur_id, matiere_id) 
                        VALUES (%s, %s)
                        """, (user_id, lacune_id))

                    # Insertion des paramètres initiaux (ignorer si déjà existant)
                    execute("""
                        INSERT IGNORE INTO parametres (utilisateur_id) VALUES (%s)
                    """, (user_id,))

                    # Insertion des disponibilités
                    for i, jour in enumerate(dispo_jours):
                        if jour and i < len(dispo_debuts) and i < len(dispo_fins) and dispo_debuts[i] and dispo_fins[i]:
                            execute("""
                                INSERT INTO disponibilites (utilisateur_id, jour_semaine, heure_debut, heure_fin)
                                VALUES (%s, %s, %s, %s)
                            """, (user_id, jour, dispo_debuts[i], dispo_fins[i]))

                    # Envoyer l'email de confirmation
                    lien = envoyer_email_confirmation(email, prenom)

                    if current_app.config.get('MAIL_SUPPRESS_SEND'):
                        return render_template('auth/email_envoye.html', confirmation_link=lien)
                    return redirect(url_for('auth.email_envoye'))
                else:
                    error = "Une erreur s'est produite lors de la création de votre compte."
                    
            except Exception as e:
                error = "Email ou téléphone déjà utilisé"
                current_step = '1'

    return render_template('auth/register.html', error=error, filieres=filieres, niveaux=niveaux, matieres=matieres, current_step=current_step, form_data=form_data)

@auth_bp.route('/email-envoye')
def email_envoye():
    return render_template('auth/email_envoye.html')

@auth_bp.route('/confirmer-email/<token>')
def confirmer_email(token):
    email = verify_token(token)
    if not email:
        return render_template('auth/email_confirme.html', error=True)
    
    try:
        execute("""
            UPDATE utilisateurs SET email_verifie = 1
            WHERE email = %s
        """, (email,))
        return render_template('auth/email_confirme.html', error=False)
    except Exception as e:
        return render_template('auth/email_confirme.html', error=True)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))