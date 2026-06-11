from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from db.database import fetch_all, fetch_one, execute
from utils.responses import get_user_context
from utils.csrf import csrf_required

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    filtre = request.args.get('filtre', 'toutes')
        
    try:
        # 1. Récupération de l'historique des notifications de l'utilisateur
        if filtre == 'match_demande':
            notifs = fetch_all("""
                SELECT * FROM notifications
                WHERE utilisateur_id = %s AND type_notification = 'match_demande'
                ORDER BY cree_le DESC
            """, (session['user_id'],))
        elif filtre == 'infos':
            notifs = fetch_all("""
                SELECT * FROM notifications
                WHERE utilisateur_id = %s AND type_notification != 'match_demande'
                ORDER BY cree_le DESC
            """, (session['user_id'],))
        else:
            notifs = fetch_all("""
                SELECT * FROM notifications
                WHERE utilisateur_id = %s
                ORDER BY cree_le DESC
            """, (session['user_id'],))
        
        # 2. Passage automatique de toutes ses notifications au statut "lu"
        execute("""
            UPDATE notifications SET est_lu = 1
            WHERE utilisateur_id = %s
        """, (session['user_id'],))
        
        context = get_user_context()
        context['notifications'] = notifs
        context['filtre'] = filtre
        return render_template('notifications/index.html', **context)
        
    except Exception as e:
        return f"Erreur lors du chargement des notifications: {str(e)}", 500


@notifications_bp.route('/notifications/repondre/<int:notif_id>/<string:action>', methods=['POST'])
@csrf_required
def repondre_notification(notif_id, action):
    """
    Route de traitement de l'action reçue depuis l'interface des notifications.
    Met à jour la table 'correspondances' en fonction du choix de l'utilisateur.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    try:
        # 1. On cherche la correspondance liée à cette notification précise
        notif = fetch_one("SELECT correspondance_id FROM notifications WHERE id = %s", (notif_id,))
        
        if notif and notif['correspondance_id']:
            id_match = notif['correspondance_id']
            
            if action == 'accepter':
                # Le destinataire accepte : le match passe au statut 1 (Validé/Accepté)
                execute("""
                    UPDATE correspondances 
                    SET statut_correspondance = 1 
                    WHERE id = %s
                """, (id_match,))
                flash("Félicitations, vous êtes officiellement mis en relation !", "success")
                
            elif action == 'refuser':
                # Le destinataire refuse : le match passe au statut 2 (Refusé/Annulé)
                execute("""
                    UPDATE correspondances 
                    SET statut_correspondance = 2 
                    WHERE id = %s
                """, (id_match,))
                flash("La proposition de mise en relation a été déclinée.", "info")
                
        return redirect(url_for('notifications.notifications'))
        
    except Exception as e:
        return f"Erreur lors du traitement de la réponse : {str(e)}", 500