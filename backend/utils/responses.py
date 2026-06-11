from flask import session
from db.database import get_db

def get_user_context():
    """Retourne les infos communes à toutes les pages (notifs non lues, user)"""
    if 'user_id' not in session:
        return {}
        
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # 1. Récupération de l'utilisateur avec sa filière
                cursor.execute("""
                    SELECT u.*, f.nom as filiere_nom
                    FROM utilisateurs u
                    LEFT JOIN filieres_etudes f ON f.id = u.id_filiere
                    WHERE u.id = %s
                """, (session['user_id'],))
                user = cursor.fetchone()
                
                # 2. Récupération du nombre de notifications non lues
                cursor.execute("""
                    SELECT COUNT(*) as nb FROM notifications
                    WHERE utilisateur_id = %s AND est_lu = 0
                """, (session['user_id'],))
                notifs = cursor.fetchone()
                
                nb_notifs = 0
                if notifs:
                    if isinstance(notifs, dict):
                        nb_notifs = notifs.get('nb', 0)
                    elif isinstance(notifs, (tuple, list)):
                        nb_notifs = notifs[0]

                return {
                    'user': user,
                    'nb_notifs': nb_notifs
                }
    except Exception as e:
        print(f"Erreur contexte utilisateur : {str(e)}")
        return {}