from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from services.matching_service import obtenir_suggestions_matching
from services.notification_service import creer_notification
from db.database import fetch_one, fetch_all, execute
from utils.responses import get_user_context
from utils.csrf import csrf_required

matching_bp = Blueprint('matching', __name__)

# =====================================================================
# 1. PARCOURS AUTOMATIQUE & AFFICHAGE HISTORIQUE (Vue unifiée)
# =====================================================================
@matching_bp.route('/matching')
def matching():
    """
    Affiche la page de matching divisée en deux flux :
    - Le Top 4 des recommandations algorithmiques (Profils non encore contactés).
    - L'historique des interactions physiques réelles (En attente ou Acceptées).
    """
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    utilisateur_id = session['user_id']
    role_actuel = request.args.get('role', 'mentee')
    if role_actuel not in ['mentor', 'mentee']:
        role_actuel = 'mentee'
        
    try:
        # On récupère les correspondances actives de l'utilisateur
        # statut=0 : en attente, statut=1 : accepté (statut=2 exclu = refusé)
        matchs_physiques = fetch_all("""
            SELECT c.id, c.score_compatibilite, c.statut_correspondance, c.initiateur_id,
                   c.mentor_id, c.mentee_id,
                   u.id AS partenaire_id, u.prenom, u.nom, u.avatar_url, f.nom as filiere, n.nom as niveau
            FROM correspondances c
            JOIN utilisateurs u ON (CASE 
                WHEN c.mentor_id = %s THEN c.mentee_id 
                ELSE c.mentor_id 
            END) = u.id
            JOIN filieres_etudes f ON u.id_filiere = f.id
            JOIN niveaux_etudes n ON u.id_niveau = n.id
            WHERE (c.mentor_id = %s OR c.mentee_id = %s) 
              AND c.statut_correspondance != 2
            ORDER BY c.id DESC
        """, (utilisateur_id, utilisateur_id, utilisateur_id))
        
        # Enrichir les matchs avec les détails de compatibilité (sans recalculer tout le matching)
        for m in matchs_physiques:
            m['score_compatibilite'] = float(m['score_compatibilite'])
            rows = fetch_all("""
                SELECT DISTINCT mat.nom FROM matieres mat
                JOIN competences_utilisateur cu ON cu.matiere_id = mat.id AND cu.utilisateur_id = %s
                JOIN difficultes_utilisateur du ON du.matiere_id = mat.id AND du.utilisateur_id = %s
            """, (m['mentor_id'], m['mentee_id']))
            m['commun_matieres'] = [r['nom'] for r in rows]
            dispo_rows = fetch_all("""
                SELECT DISTINCT d1.jour_semaine, d1.heure_debut, d1.heure_fin
                FROM disponibilites d1
                JOIN disponibilites d2 ON d1.jour_semaine = d2.jour_semaine
                    AND d1.heure_debut < d2.heure_fin
                    AND d1.heure_fin > d2.heure_debut
                WHERE d1.utilisateur_id = %s AND d2.utilisateur_id = %s
            """, (m['mentor_id'], m['mentee_id']))
            m['commun_dispos'] = []
            for d in dispo_rows:
                m['commun_dispos'].append({
                    'jour_semaine': d['jour_semaine'],
                    'heure_debut': str(d['heure_debut'])[:5],
                    'heure_fin': str(d['heure_fin'])[:5],
                })
        
        # Séparation des correspondances pour le rendu
        matchs_en_attente = [m for m in matchs_physiques if m['statut_correspondance'] == 0]
        matchs_acceptes = [m for m in matchs_physiques if m['statut_correspondance'] == 1]
        
        context = get_user_context()
        context.update({
            'mentors': [],
            'role_actuel': role_actuel,
            'matchs_en_attente': matchs_en_attente,
            'matchs_acceptes': matchs_acceptes
        })
        return render_template('matching/index.html', **context)
        
    except Exception as e:
        return f"Erreur lors du chargement des correspondances: {str(e)}", 500


# =====================================================================
# 2. PARCOURS CATALOGUE : CLIC SUR UNE OFFRE / DEMANDE
# =====================================================================
@matching_bp.route('/faire_match/<string:type_annonce>/<int:annonce_id>', methods=['POST'])
@csrf_required
def faire_match(type_annonce, annonce_id):
    """
    Intercepte le clic sur le catalogue, calcule l'affinité, 
    crée la correspondance (Statut 0 = En attente), notifie le destinataire 
    et redirige instantanément vers l'onglet matching.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    connecte_id = session['user_id']
    nom_expediteur = f"{session.get('prenom', 'Un étudiant')} {session.get('nom', '')}"
    
    try:
        if type_annonce == 'offre':
            role_matching = 'mentee'
            annonce = fetch_one("SELECT utilisateur_id FROM offre_mentorat WHERE id = %s AND statut_offre = 1", (annonce_id,))
            if not_annonce_valide(annonce, connecte_id):
                flash("Cette offre n'est plus disponible.", "warning")
                return redirect(url_for('offres.offres'))
                
            mentor_id = annonce['utilisateur_id']
            mentee_id = connecte_id
            destinataire_id = mentor_id
            message_notif = f"{nom_expediteur} a sollicité votre offre de mentorat ! Souhaitez-vous accepter le match ?"
            
        elif type_annonce == 'demande':
            role_matching = 'mentor'
            annonce = fetch_one("SELECT utilisateur_id FROM demande_mentorat WHERE id = %s AND statut_demande = 1", (annonce_id,))
            if not_annonce_valide(annonce, connecte_id):
                flash("Cette demande n'est plus disponible.", "warning")
                return redirect(url_for('demandes.demandes'))
                
            mentor_id = connecte_id
            mentee_id = annonce['utilisateur_id']
            destinataire_id = mentee_id
            message_notif = f"{nom_expediteur} propose de répondre à votre demande d'accompagnement ! Souhaitez-vous accepter ?"
            
        else:
            return "Action non autorisée", 400

        # Calcul automatique du score pour l'historiser
        score_final = 0.00
        suggestions = obtenir_suggestions_matching(connecte_id, role=role_matching)
        for sug in suggestions:
            if sug['id'] == destinataire_id:
                score_final = sug['score_compatibilite']
                break

        # Sauvegarde initiale : État 0 (En attente)
        correspondance_id = execute("""
            INSERT INTO correspondances (mentor_id, mentee_id, score_compatibilite, statut_correspondance, initiateur_id)
            VALUES (%s, %s, %s, 0, %s)
        """, (mentor_id, mentee_id, score_final, connecte_id))
        
        # Récupération de l'ID généré si nécessaire
        if not correspondance_id:
            recup = fetch_one("""
                SELECT id FROM correspondances 
                WHERE mentor_id = %s AND mentee_id = %s AND statut_correspondance = 0 AND initiateur_id = %s
                ORDER BY id DESC LIMIT 1
            """, (mentor_id, mentee_id, connecte_id))
            id_match = recup['id'] if recup else None
        else:
            id_match = correspondance_id

        if id_match:
            creer_notification(
                utilisateur_id=destinataire_id,
                message=message_notif,
                type_notification="match_demande",
                correspondance_id=id_match
            )
            
        flash("Votre demande de mise en relation a été enregistrée. Suivez son statut ici !", "success")
        return redirect(url_for('matching.matching'))
        
    except Exception as e:
        return f"Erreur lors de l'enregistrement de la mise en relation : {str(e)}", 500


# =====================================================================
# 3. TRAITEMENT DE LA DÉCISION (Boutons Accepter / Refuser)
# =====================================================================
@matching_bp.route('/traiter_match/<string:action>/<int:correspondance_id>', methods=['POST'])
@csrf_required
def traiter_match(action, correspondance_id):
    """
    Route synchrone de décision : Modifie le statut en BDD (1=Accepté, 2=Refusé).
    Si l'action est 'refuser', le statut devient 2, ce qui provoquera 
    le retrait immédiat de l'affichage lors du rechargement automatique.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    connecte_id = session['user_id']
    
    try:
        # Détermination de l'état : 1 si accepté, 2 si refusé
        nouveau_statut = 1 if action == 'accepter' else 2
        
        # Sécurité : On s'assure que l'utilisateur qui clique n'est pas l'initiateur de l'action
        execute("""
            UPDATE correspondances 
            SET statut_correspondance = %s 
            WHERE id = %s AND (mentor_id = %s OR mentee_id = %s) AND initiateur_id != %s
        """, (nouveau_statut, correspondance_id, connecte_id, connecte_id, connecte_id))
        
        if action == 'accepter':
            flash("Félicitations ! Le match est validé. Retrouvez vos coordonnées mutuelles.", "success")
        else:
            flash("La demande a été refusée. Le profil a été retiré de votre espace.", "info")
            
        return redirect(url_for('matching.matching'))
        
    except Exception as e:
        return f"Erreur lors du traitement du match : {str(e)}", 500


@matching_bp.route('/envoyer_demande', methods=['POST'])
@csrf_required
def envoyer_demande():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    connecte_id = session['user_id']
    mentor_id = int(request.form.get('mentor_id', 0))
    mentee_id = int(request.form.get('mentee_id', 0))
    score = float(request.form.get('score', 0))

    if not mentor_id or not mentee_id:
        flash("Informations de match invalides.", "warning")
        return redirect(request.referrer or url_for('matching.matching'))

    # Vérification : pas de correspondance existante (pending ou acceptée)
    existante = fetch_one("""
        SELECT id FROM correspondances
        WHERE ((mentor_id = %s AND mentee_id = %s) OR (mentor_id = %s AND mentee_id = %s))
          AND statut_correspondance IN (0, 1)
    """, (mentor_id, mentee_id, mentee_id, mentor_id))
    if existante:
        flash("Une demande est déjà en cours avec cette personne.", "info")
        return redirect(url_for('matching.matching'))

    # Déterminer le rôle : si l'utilisateur est le mentor, il offre son aide (role='mentor')
    # S'il est le mentee, il demande de l'aide (role='mentee')
    role = 'mentor' if connecte_id == mentor_id else 'mentee'
    nom_expediteur = f"{session.get('prenom', 'Un étudiant')} {session.get('nom', '')}"
    destinataire_id = mentee_id if connecte_id == mentor_id else mentor_id

    try:
        # Recalcul du score via le service de matching selon le rôle
        suggestions = obtenir_suggestions_matching(connecte_id, role=role)
        for sug in suggestions:
            if role == 'mentor' and sug['id'] == mentee_id:
                score = sug['score_compatibilite']
                break
            elif role == 'mentee' and sug['id'] == mentor_id:
                score = sug['score_compatibilite']
                break

        correspondance_id = execute("""
            INSERT INTO correspondances (mentor_id, mentee_id, score_compatibilite, statut_correspondance, initiateur_id)
            VALUES (%s, %s, %s, 0, %s)
        """, (mentor_id, mentee_id, score, connecte_id))

        if not correspondance_id:
            recup = fetch_one("""
                SELECT id FROM correspondances
                WHERE mentor_id = %s AND mentee_id = %s AND initiateur_id = %s
                ORDER BY id DESC LIMIT 1
            """, (mentor_id, mentee_id, connecte_id))
            id_match = recup['id'] if recup else None
        else:
            id_match = correspondance_id

        if id_match:
            message = f"{nom_expediteur} souhaite vous offrir son aide en mentorat !" if role == 'mentor' else f"{nom_expediteur} a besoin de votre aide !"
            creer_notification(
                utilisateur_id=destinataire_id,
                message=message,
                type_notification="match_demande",
                correspondance_id=id_match
            )

        flash("Votre demande de mise en relation a été envoyée !", "success")
    except Exception as e:
        flash(f"Erreur lors de l'envoi : {str(e)}", "danger")

    return redirect(url_for('matching.matching'))


def not_annonce_valide(annonce, connecte_id):
    return not annonce or annonce['utilisateur_id'] == connecte_id