from flask import Blueprint, render_template, request, session, redirect, url_for
from db.database import fetch_all, fetch_one, execute
from utils.responses import get_user_context
from utils.csrf import csrf_required

conversations_bp = Blueprint('conversations', __name__)


@conversations_bp.route('/conversations')
def conversations():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    try:
        convs = fetch_all("""
            SELECT c.id, DATE_FORMAT(c.cree_le, '%%Y-%%m-%%d') as cree_le,
                   u.prenom, u.nom, u.avatar_url
            FROM conversations c
            JOIN participants_conversation pc ON pc.conversation_id = c.id
            JOIN participants_conversation pc2 ON pc2.conversation_id = c.id
            JOIN utilisateurs u ON u.id = pc2.utilisateur_id
            WHERE pc.utilisateur_id = %s AND pc2.utilisateur_id != %s
        """, (session['user_id'], session['user_id']))

        context = get_user_context()
        context['conversations'] = convs
        return render_template('conversations/index.html', **context)

    except Exception as e:
        return f"Erreur lors du chargement des conversations: {str(e)}", 500


@conversations_bp.route('/conversations/avec/<int:contact_id>')
def demarrer_conversation(contact_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    if contact_id == user_id:
        return redirect(url_for('conversations.conversations'))

    try:
        conv = fetch_one("""
            SELECT c.id FROM conversations c
            JOIN participants_conversation p1 ON p1.conversation_id = c.id AND p1.utilisateur_id = %s
            JOIN participants_conversation p2 ON p2.conversation_id = c.id AND p2.utilisateur_id = %s
        """, (user_id, contact_id))

        if conv:
            return redirect(url_for('conversations.conversation', conv_id=conv['id']))

        conv_id = execute("INSERT INTO conversations () VALUES ()")
        execute("INSERT INTO participants_conversation (conversation_id, utilisateur_id) VALUES (%s, %s)", (conv_id, user_id))
        execute("INSERT INTO participants_conversation (conversation_id, utilisateur_id) VALUES (%s, %s)", (conv_id, contact_id))

        return redirect(url_for('conversations.conversation', conv_id=conv_id))
    except Exception as e:
        return f"Erreur lors de la création de la conversation: {str(e)}", 500


@conversations_bp.route('/conversations/<int:conv_id>', methods=['GET', 'POST'])
@csrf_required
def conversation(conv_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Vérification que l'utilisateur est bien participant
    try:
        participant = fetch_one("""
            SELECT 1 AS existe FROM participants_conversation
            WHERE conversation_id = %s AND utilisateur_id = %s
        """, (conv_id, session['user_id']))

        if not participant:
            return render_template('errors/403.html'), 403

    except Exception as e:
        return f"Erreur de vérification d'accès: {str(e)}", 500

    error = None
    messages = []

    # 1. Traitement de l'envoi d'un nouveau message
    if request.method == 'POST':
        try:
            contenu = request.form['contenu'].strip()
            if contenu:
                execute("""
                    INSERT INTO messages (conversation_id, expediteur_id, contenu)
                    VALUES (%s, %s, %s)
                """, (conv_id, session['user_id'], contenu))
                return redirect(url_for('conversations.conversation', conv_id=conv_id))
        except Exception as e:
            error = f"Erreur lors de l'envoi du message: {str(e)}"

    # 2. Chargement de l'historique des messages
    try:
        messages = fetch_all("""
            SELECT m.*, u.prenom, u.nom, u.avatar_url
            FROM messages m
            JOIN utilisateurs u ON u.id = m.expediteur_id
            WHERE m.conversation_id = %s
            ORDER BY m.envoye_le ASC
        """, (conv_id,))
    except Exception as e:
        error = f"Erreur lors du chargement des messages: {str(e)}"

    contact = fetch_one("""
        SELECT u.id, u.prenom, u.nom, u.avatar_url FROM participants_conversation pc
        JOIN utilisateurs u ON u.id = pc.utilisateur_id
        WHERE pc.conversation_id = %s AND pc.utilisateur_id != %s
        LIMIT 1
    """, (conv_id, session['user_id']))
    ctx = get_user_context()
    ctx.update({'messages': messages, 'conv_id': conv_id, 'error': error, 'contact': contact})
    return render_template('conversations/index.html', **ctx)