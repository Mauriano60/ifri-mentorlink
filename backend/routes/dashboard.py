from flask import Blueprint, render_template, session
from utils.decorators import login_required
from db.database import fetch_one, fetch_all

dashboard_bp = Blueprint('dashboard', __name__)


def get_dashboard_data(user_id):
    try:
        nb_correspondances = fetch_one("""
            SELECT COUNT(*) AS total FROM correspondances
            WHERE (mentor_id = %s OR mentee_id = %s)
            AND statut_correspondance = 1
        """, (user_id, user_id))['total']

        nb_messages_non_lus = fetch_one("""
            SELECT COUNT(*) AS total FROM messages m
            JOIN participants_conversation pc 
                ON pc.conversation_id = m.conversation_id
            WHERE pc.utilisateur_id = %s 
            AND m.expediteur_id != %s
        """, (user_id, user_id))['total']

        nb_offres = fetch_one("""
            SELECT COUNT(*) AS total FROM offre_mentorat o
            JOIN utilisateurs u ON o.utilisateur_id = u.id
            WHERE u.id_filiere = (
                SELECT id_filiere FROM utilisateurs WHERE id = %s
            )
            AND o.utilisateur_id != %s
            AND o.statut_offre = 1
        """, (user_id, user_id))['total']

        nb_demandes = fetch_one("""
            SELECT COUNT(*) AS total FROM demande_mentorat d
            WHERE d.matiere_id IN (
                SELECT matiere_id FROM competences_utilisateur
                WHERE utilisateur_id = %s
            )
            AND d.utilisateur_id != %s
            AND d.statut_demande = 1
        """, (user_id, user_id))['total']

        activites = fetch_all("""
            SELECT message, type_notification, cree_le
            FROM notifications
            WHERE utilisateur_id = %s
            ORDER BY cree_le DESC
            LIMIT 5
        """, (user_id,))

        meilleurs_matchs = fetch_all("""
            SELECT u.prenom, u.nom, u.avatar_url,
                   f.nom AS filiere, n.nom AS niveau,
                   c.score_compatibilite
            FROM correspondances c
            JOIN utilisateurs u ON (
                CASE WHEN c.mentor_id = %s 
                     THEN c.mentee_id
                     ELSE c.mentor_id END = u.id
            )
            JOIN filieres_etudes f ON u.id_filiere = f.id
            JOIN niveaux_etudes n ON u.id_niveau = n.id
            WHERE (c.mentor_id = %s OR c.mentee_id = %s)
            ORDER BY c.score_compatibilite DESC
            LIMIT 3
        """, (user_id, user_id, user_id))

        publications = fetch_all("""
            SELECT 'offre' AS type, m.nom AS matiere,
                   o.format, o.description, o.cree_le
            FROM offre_mentorat o
            JOIN matieres m ON o.matiere_id = m.id
            WHERE o.utilisateur_id = %s AND o.statut_offre = 1

            UNION ALL

            SELECT 'demande' AS type, m.nom AS matiere,
                   d.format, d.description, d.cree_le
            FROM demande_mentorat d
            JOIN matieres m ON d.matiere_id = m.id
            WHERE d.utilisateur_id = %s AND d.statut_demande = 1

            ORDER BY cree_le DESC
            LIMIT 5
        """, (user_id, user_id))

        return {
            'nb_correspondances': nb_correspondances,
            'nb_messages_non_lus': nb_messages_non_lus,
            'nb_offres': nb_offres,
            'nb_demandes': nb_demandes,
            'activites': activites,
            'meilleurs_matchs': meilleurs_matchs,
            'publications': publications
        }

    except Exception as e:
        return {
            'nb_correspondances': 0,
            'nb_messages_non_lus': 0,
            'nb_offres': 0,
            'nb_demandes': 0,
            'activites': [],
            'meilleurs_matchs': [],
            'publications': []
        }


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session.get('user_id')
    data = get_dashboard_data(user_id)
    return render_template('mentore/dashboard.html', **data)