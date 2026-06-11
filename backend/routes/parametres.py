import os
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from db.database import fetch_all, fetch_one, execute
from utils.validators import valider_competences_et_lacunes, valider_email, valider_telephone
from utils.responses import get_user_context
from utils.csrf import csrf_required
from werkzeug.utils import secure_filename

settings_bp = Blueprint('settings', __name__)

# =====================================================================
# 1. NOUVELLE ROUTE : MODIFICATION DES COMPÉTENCES ET LACUNES
# =====================================================================
@settings_bp.route('/settings/profil', methods=['GET', 'POST'])
@csrf_required
def modifier_profil_matieres():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    error = None
    success = None
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    try:
        if request.method == 'POST':
            prenom = request.form.get('prenom', '').strip()
            nom = request.form.get('nom', '').strip()
            biographie = request.form.get('biographie', '').strip()
            id_filiere = request.form.get('id_filiere')
            id_niveau = request.form.get('id_niveau')
            
            if not prenom or not nom:
                error = "Prénom et nom obligatoires"
            else:
                avatar_url = None
                avatar_file = request.files.get('avatar')
                if avatar_file and avatar_file.filename:
                    ext = avatar_file.filename.rsplit('.', 1)[-1].lower() if '.' in avatar_file.filename else ''
                    if ext not in ALLOWED_EXTENSIONS:
                        error = "Format d'image non autorisé (PNG, JPG, WEBP)"
                    elif avatar_file.content_length and avatar_file.content_length > 2 * 1024 * 1024:
                        error = "L'image ne doit pas dépasser 2 Mo"
                    else:
                        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
                        os.makedirs(upload_dir, exist_ok=True)
                        filename = f"user_{user_id}_{secure_filename(avatar_file.filename)}"
                        avatar_file.save(os.path.join(upload_dir, filename))
                        avatar_url = f"uploads/avatars/{filename}"

                if not error:
                    if avatar_url:
                        execute("""
                            UPDATE utilisateurs SET prenom=%s, nom=%s, avatar_url=%s, biographie=%s,
                                                    id_filiere=%s, id_niveau=%s
                            WHERE id=%s
                        """, (prenom, nom, avatar_url, biographie, id_filiere, id_niveau, user_id))
                    else:
                        execute("""
                            UPDATE utilisateurs SET prenom=%s, nom=%s, biographie=%s,
                                                    id_filiere=%s, id_niveau=%s
                            WHERE id=%s
                        """, (prenom, nom, biographie, id_filiere, id_niveau, user_id))
                    session['prenom'] = prenom
                    session['nom'] = nom
                    success = "Informations mises à jour avec succès."

            competences = request.form.getlist('competences')
            lacunes = request.form.getlist('lacunes')
            
            if competences or lacunes:
                est_valide, message_erreur = valider_competences_et_lacunes(competences, lacunes)
                if not est_valide:
                    error = message_erreur
                else:
                    execute("DELETE FROM competences_utilisateur WHERE utilisateur_id = %s", (user_id,))
                    execute("DELETE FROM difficultes_utilisateur WHERE utilisateur_id = %s", (user_id,))
                    for comp_id in competences:
                        execute("INSERT INTO competences_utilisateur (utilisateur_id, matiere_id) VALUES (%s, %s)", (user_id, comp_id))
                    for lacune_id in lacunes:
                        execute("INSERT INTO difficultes_utilisateur (utilisateur_id, matiere_id) VALUES (%s, %s)", (user_id, lacune_id))
                    if not error:
                        success = "Compétences et lacunes mises à jour."

            # Sauvegarde des disponibilités
            jours = request.form.getlist('jour[]')
            heures_debut = request.form.getlist('heure_debut[]')
            heures_fin = request.form.getlist('heure_fin[]')
            if jours and heures_debut and heures_fin:
                execute("DELETE FROM disponibilites WHERE utilisateur_id = %s", (user_id,))
                for i, jour in enumerate(jours):
                    if jour and i < len(heures_debut) and i < len(heures_fin) and heures_debut[i] and heures_fin[i]:
                        execute("""
                            INSERT INTO disponibilites (utilisateur_id, jour_semaine, heure_debut, heure_fin)
                            VALUES (%s, %s, %s, %s)
                        """, (user_id, jour, heures_debut[i], heures_fin[i]))

        toutes_matieres = fetch_all("SELECT * FROM matieres ORDER BY nom ASC")
        filieres = fetch_all("SELECT * FROM filieres_etudes ORDER BY nom")
        niveaux = fetch_all("SELECT * FROM niveaux_etudes ORDER BY nom")
        res_comp = fetch_all("SELECT matiere_id FROM competences_utilisateur WHERE utilisateur_id = %s", (user_id,))
        ids_competences_actuelles = [rc['matiere_id'] for rc in res_comp]
        res_lac = fetch_all("SELECT matiere_id FROM difficultes_utilisateur WHERE utilisateur_id = %s", (user_id,))
        ids_lacunes_actuelles = [rl['matiere_id'] for rl in res_lac]
        disponibilites = fetch_all("""
            SELECT jour_semaine, heure_debut, heure_fin FROM disponibilites
            WHERE utilisateur_id = %s
            ORDER BY FIELD(jour_semaine, 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche')
        """, (user_id,))

    except Exception as e:
        toutes_matieres = []; filieres = []; niveaux = []
        ids_competences_actuelles = []; ids_lacunes_actuelles = []; disponibilites = []
        error = f"Erreur : {str(e)}"
        
    ctx = get_user_context()
    ctx.update({
        'matieres': toutes_matieres,
        'filieres': filieres,
        'niveaux': niveaux,
        'mes_competences': ids_competences_actuelles,
        'mes_lacunes': ids_lacunes_actuelles,
        'disponibilites': disponibilites,
        'error': error,
        'success': success
    })
    return render_template('settings/profil_matieres.html', **ctx)


# =====================================================================
# 2. VOS ROUTES EXISTANTES (CONSERVÉES À 100% SANS ALTERATION)
# =====================================================================
@settings_bp.route('/settings/preferences', methods=['GET', 'POST'])
@csrf_required
def preferences():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    error = None
    success = None
    
    try:
        if request.method == 'POST':
            email_notif = 1 if 'email_notification' in request.form else 0
            push_notif  = 1 if 'push_notification' in request.form else 0
            match_notif = 1 if 'new_match_alerts' in request.form else 0
            weekly_notif = 1 if 'weekly_summary' in request.form else 0
            
            execute("""
                UPDATE parametres 
                SET email_notification = %s, 
                    push_notification = %s, 
                    new_match_alerts = %s, 
                    weekly_summary = %s
                WHERE utilisateur_id = %s
            """, (email_notif, push_notif, match_notif, weekly_notif, session['user_id']))
            
            success = "Préférences de notification mises à jour"
            
        params = fetch_one("SELECT * FROM parametres WHERE utilisateur_id = %s", (session['user_id'],))
        
    except Exception as e:
        params = None
        error = f"Erreur lors du cachement des préférences: {str(e)}"
        
    ctx = get_user_context()
    ctx.update({'params': params, 'error': error, 'success': success})
    return render_template('settings/preferences.html', **ctx)


@settings_bp.route('/settings/confidentialite', methods=['GET', 'POST'])
@csrf_required
def confidentialite():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    error = None
    success = None
    
    try:
        if request.method == 'POST':
            visibilite = request.form['visibilite_profil']
            
            execute("""
                UPDATE parametres SET visibilite_profil=%s
                WHERE utilisateur_id=%s
            """, (visibilite, session['user_id']))
            
            success = "Paramètres de confidentialité mis à jour"
            
        params = fetch_one("SELECT * FROM parametres WHERE utilisateur_id=%s", (session['user_id'],))
        
    except Exception as e:
        params = None
        error = f"Erreur lors de la mise à jour des paramètres: {str(e)}"
        
    ctx = get_user_context()
    ctx.update({'params': params, 'error': error, 'success': success})
    return render_template('settings/confidentialite.html', **ctx)


@settings_bp.route('/settings/supprimer-compte', methods=['GET', 'POST'])
@csrf_required
def supprimer_compte():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    error = None
    
    if request.method == 'POST':
        try:
            uid = session['user_id']
            execute("UPDATE correspondances SET statut_correspondance=2 WHERE mentor_id=%s OR mentee_id=%s", (uid, uid))
            execute("UPDATE offre_mentorat SET statut_offre=0 WHERE utilisateur_id=%s", (uid,))
            execute("UPDATE demande_mentorat SET statut_demande=0 WHERE utilisateur_id=%s", (uid,))
            execute("UPDATE utilisateurs SET est_actif=0 WHERE id=%s", (uid,))
            session.pop('user_id', None)
            session.pop('prenom', None)
            session.pop('nom', None)
            flash("Votre compte a été supprimé avec succès.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            error = f"Erreur lors du traitement : {str(e)}"

    ctx = get_user_context()
    ctx['error'] = error
    return render_template('settings/supprimer-compte.html', **ctx)