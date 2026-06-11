from flask import Flask, session
from config.settings import Config
from services.mail_service import mail
from flask_socketio import SocketIO, join_room
from extensions import limiter
from datetime import datetime

socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(Config)
    app.config['SERVER_NAME'] = '127.0.0.1:5000'
    app.config['APPLICATION_ROOT'] = '/'
    app.config['PREFERRED_URL_SCHEME'] = 'http'
    
    mail.init_app(app)
    limiter.init_app(app)

    from utils.csrf import generer_token_csrf

    @app.context_processor
    def inject_csrf():
        return dict(csrf_token=generer_token_csrf)

    @app.after_request
    def inject_socketio(response):
        if response.content_type and 'text/html' in response.content_type:
            tag = b'<script src="/static/js/socketio-client.js"></script>\n</body>'
            response.data = response.data.replace(b'</body>', tag)
            response.headers['Content-Length'] = len(response.data)
        return response

    from routes.auth import auth_bp
    from routes.users import users_bp
    from routes.matching import matching_bp
    from routes.conversations import conversations_bp
    from routes.notifications import notifications_bp
    from routes.offres import offres_bp
    from routes.demandes import demandes_bp
    from routes.parametres import settings_bp
    from routes.references import references_bp
    from routes.email import email_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(offres_bp)
    app.register_blueprint(demandes_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(references_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(dashboard_bp)

    return app

app = create_app()
socketio.init_app(app)

from db.database import fetch_one, fetch_all, execute

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        utilisateur_id = session['user_id']
        join_room(f"user_{utilisateur_id}")
        print(f"Utilisateur {utilisateur_id} connecté au canal temps réel.")

@socketio.on('join_conversation')
def handle_join_conv(conv_id):
    room = f"conv_{conv_id}"
    join_room(room)
    print(f"Utilisateur {session.get('user_id')} a rejoint la conversation {conv_id}.")

@socketio.on('send_message')
def handle_send_message(data):
    user_id = session.get('user_id')
    if not user_id:
        return {'erreur': 'Non authentifié'}
    conv_id = data.get('conv_id')
    contenu = data.get('contenu', '').strip()
    if not conv_id or not contenu:
        return {'erreur': 'Données invalides'}
    participant = fetch_one("""
        SELECT 1 FROM participants_conversation
        WHERE conversation_id = %s AND utilisateur_id = %s
    """, (conv_id, user_id))
    if not participant:
        return {'erreur': 'Accès refusé'}
    execute("""
        INSERT INTO messages (conversation_id, expediteur_id, contenu)
        VALUES (%s, %s, %s)
    """, (conv_id, user_id, contenu))
    user = fetch_one("SELECT prenom, nom, avatar_url FROM utilisateurs WHERE id = %s", (user_id,))
    now = datetime.now().strftime('%H:%M')
    socketio.emit('new_message', {
        'expediteur_id': user_id,
        'prenom': user['prenom'],
        'nom': user['nom'],
        'avatar_url': user.get('avatar_url') or '',
        'contenu': contenu,
        'heure': now
    }, room=f"conv_{conv_id}")

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)