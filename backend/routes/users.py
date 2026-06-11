from flask import Blueprint, render_template, session, redirect, url_for
from db.database import fetch_all, fetch_one
from utils.decorators import login_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/dashboard')
@login_required
def dashboard():
    from utils.responses import get_user_context
    
    try:
        user_id = session['user_id']

        # Récupérer la filière de l'étudiant connecté pour filtrer les offres
        user_info = fetch_one("SELECT id_filiere FROM utilisateurs WHERE id = %s", (user_id,))
        id_filiere = user_info['id_filiere'] if user_info else None

        # ==========================================
        # 1. CALCUL DES COMPTEURS (STATISTIQUES)
        # ==========================================

        # A. Nombre d'offres disponibles dans sa filière (exclure ses propres offres)
        nb_offres_filiere = 0
        if id_filiere:
            res_offres = fetch_one("""
                SELECT COUNT(o.id) as total 
                FROM offre_mentorat o
                JOIN utilisateurs u ON u.id = o.utilisateur_id
                WHERE u.id_filiere = %s AND o.utilisateur_id != %s AND o.statut_offre = 1
            """, (id_filiere, user_id))
            nb_offres_filiere = res_offres['total'] if res_offres else 0

        # B. Nombre de demandes correspondantes à son profil
        res_demandes = fetch_one("""
            SELECT COUNT(d.id) as total 
            FROM demande_mentorat d
            JOIN competences_utilisateur cu ON cu.matiere_id = d.matiere_id
            WHERE cu.utilisateur_id = %s AND d.utilisateur_id != %s AND d.statut_demande = 1
        """, (user_id, user_id))
        nb_demandes_profil = res_demandes['total'] if res_demandes else 0

        # C. Nombre total de correspondances (matchs) pour cet utilisateur
        res_matches = fetch_one("""
            SELECT COUNT(id) as total FROM correspondances WHERE mentee_id = %s OR mentor_id = %s
        """, (user_id, user_id))
        nb_correspondances = res_matches['total'] if res_matches else 0

        # D. Nombre de messages reçus par l'utilisateur (échange dans ses conversations)
        res_messages = fetch_one("""
            SELECT COUNT(m.id) as total 
            FROM messages m
            JOIN participants_conversation pc ON pc.conversation_id = m.conversation_id
            WHERE pc.utilisateur_id = %s AND m.expediteur_id != %s
        """, (user_id, user_id))
        nb_messages_non_lus = res_messages['total'] if res_messages else 0


        # ==========================================
        # 2. SECTIONS DE CONTENU & FLUX
        # ==========================================

        # E. Ses meilleurs matchs (Top 5 des mentors/tutorés compatibles)
        meilleurs_matchs = fetch_all("""
            SELECT c.score_compatibilite, u.id, u.prenom, u.nom, u.avatar_url,
                   f.nom as filiere, n.nom as niveau
            FROM correspondances c
            JOIN utilisateurs u ON u.id = c.mentor_id
            JOIN filieres_etudes f ON f.id = u.id_filiere
            JOIN niveaux_etudes n ON n.id = u.id_niveau
            WHERE c.mentee_id = %s AND c.statut_correspondance != 2 AND u.est_actif = 1
            ORDER BY c.score_compatibilite DESC LIMIT 5
        """, (user_id,))

        # F. Ses publications (Ses propres offres et demandes combinées avec UNION)
        ses_publications = fetch_all("""
            SELECT 'offre' as type_pub, o.id, o.description, o.cree_le, m.nom as matiere
            FROM offre_mentorat o
            JOIN matieres m ON m.id = o.matiere_id
            WHERE o.utilisateur_id = %s AND o.statut_offre = 1
            
            UNION ALL
            
            SELECT 'demande' as type_pub, d.id, d.description, d.cree_le, m.nom as matiere
            FROM demande_mentorat d
            JOIN matieres m ON m.id = d.matiere_id
            WHERE d.utilisateur_id = %s AND d.statut_demande = 1
            
            ORDER BY cree_le DESC
        """, (user_id, user_id))

        # G. Activités récentes (Les dernières notifications reçues)
        activites_recentes = fetch_all("""
            SELECT 'notification' as type_act, type_notification as contenu, cree_le 
            FROM notifications WHERE utilisateur_id = %s
            ORDER BY cree_le DESC LIMIT 5
        """, (user_id,))


        # ==========================================
        # 3. CONTEXTE ET RENDU
        # ==========================================
        context = get_user_context()
        context.update({
            'nb_offres_filiere': nb_offres_filiere,
            'nb_demandes_profil': nb_demandes_profil,
            'nb_correspondances': nb_correspondances,
            'nb_messages_non_lus': nb_messages_non_lus,
            'meilleurs_matchs': meilleurs_matchs,
            'ses_publications': ses_publications,
            'activites_recentes': activites_recentes
        })
        return render_template('dashboard/index.html', **context)
        
    except Exception as e:
        return f"Erreur lors du chargement du dashboard: {str(e)}", 500


@users_bp.route('/profil/<int:user_id>')
@login_required
def profil(user_id):
    from utils.responses import get_user_context
    
    try:
        # 1. Informations générales complètes de l'utilisateur
        profil_user = fetch_one("""
            SELECT u.id, u.nom, u.prenom, u.email, u.biographie, u.avatar_url,
                   f.nom as filiere, n.nom as niveau
            FROM utilisateurs u
            JOIN filieres_etudes f ON f.id = u.id_filiere
            JOIN niveaux_etudes n ON n.id = u.id_niveau
            WHERE u.id = %s AND u.est_actif = 1
        """, (user_id,))
        
        if not profil_user:
            return "Utilisateur introuvable", 404
            
        # 2. Compétences (Matières maîtrisées)
        # ALIGNEMENT BDD : Table utilisateur_competences
        competences = fetch_all("""
            SELECT m.nom FROM competences_utilisateur cu
            JOIN matieres m ON m.id = cu.matiere_id
            WHERE cu.utilisateur_id = %s
        """, (user_id,))

        # 3. Lacunes (Matières associées à ses difficultés)
        # ALIGNEMENT BDD : Remplacement de plus_basses_notes par utilisateur_lacunes
        lacunes = fetch_all("""
            SELECT m.nom FROM difficultes_utilisateur du
            JOIN matieres m ON m.id = du.matiere_id
            WHERE du.utilisateur_id = %s
        """, (user_id,))

        # 4. Disponibilités 
        disponibilites = fetch_all("""
            SELECT jour_semaine, heure_debut, heure_fin 
            FROM disponibilites
            WHERE utilisateur_id = %s
            ORDER BY FIELD(jour_semaine, 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche')
        """, (user_id,))

        # 5. Ses offres de mentorat actives à afficher sur son profil
        offres = fetch_all("""
            SELECT o.*, m.nom as matiere
            FROM offre_mentorat o
            JOIN matieres m ON m.id = o.matiere_id
            WHERE o.utilisateur_id = %s AND o.statut_offre = 1
        """, (user_id,))

        # Envoi au template
        context = get_user_context()
        context.update({
            'profil_user': profil_user,
            'competences': competences,
            'lacunes': lacunes,
            'disponibilites': disponibilites,
            'offres': offres
        })
        return render_template('profil/public.html', **context)
        
    except Exception as e:
        return f"Erreur lors du chargement du profil: {str(e)}", 500