from db.database import execute, fetch_one

def creer_notification(utilisateur_id, message, type_notification="info", correspondance_id=None):
    from app import socketio
    """
    Insère une notification interactive ou informative en base et déclenche 
    un signal WebSocket en temps réel.
    
    PARAMÈTRES :
    - utilisateur_id (int) : L'étudiant qui reçoit la notification.
    - message (str) : Le texte de l'alerte.
    - type_notification (str) : 'match_demande' (nécessite action), 'match_valide', 'info'.
    - correspondance_id (int, optional) : L'ID de la relation créée dans la table 'correspondances'.
    """
    try:
        # 1. Insertion en base de données avec la référence de la correspondance
        execute("""
            INSERT INTO notifications (utilisateur_id, message, type_notification, correspondance_id)
            VALUES (%s, %s, %s, %s)
        """, (utilisateur_id, message, type_notification, correspondance_id))
        
        # 2. Récupération du nombre total de notifications non lues
        result = fetch_one("""
            SELECT COUNT(*) as nb 
            FROM notifications
            WHERE utilisateur_id = %s AND est_lu = 0
        """, (utilisateur_id,))
        nb_non_lues = result['nb'] if result else 0

        # 3. Émission WebSocket avec l'ID de correspondance pour l'interaction dynamique
        socketio.emit(
            'nouvelle_notification', 
            {
                'nb_non_lues': nb_non_lues,
                'dernier_message': message,
                'type': type_notification,
                'correspondance_id': correspondance_id
            }, 
            room=f"user_{utilisateur_id}"
        )
        print(f"Notification interactive [{type_notification}] envoyée à l'utilisateur {utilisateur_id}")

    except Exception as e:
        print(f"Erreur lors de la création de la notification interactive : {str(e)}")