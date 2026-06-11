from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for

mail = Mail()

def generate_token(email, salt_type='email-confirmation'):
    """Génère un token unique lié à l'email avec un salt configurable"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=salt_type)

def verify_token(token, salt_type='email-confirmation', expiration=3600):
    """Vérifie le token et retourne l'email s'il est valide"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=salt_type, max_age=expiration)
        return email
    except Exception:
        return None

def envoyer_email_confirmation(email, prenom):
    """Envoie un email de confirmation à l'utilisateur, retourne le lien de confirmation"""
    token = generate_token(email, salt_type='email-confirmation')
    lien = url_for('auth.confirmer_email', token=token, _external=True)

    msg = Message(
        subject="Confirmez votre adresse email - IFRI_MentorLink",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.body = f"""Bonjour {prenom},

Merci de vous être inscrit sur IFRI_MentorLink !

Cliquez sur le lien ci-dessous pour confirmer votre adresse email :
{lien}

Ce lien expire dans 1 heure.

Si vous n'avez pas créé de compte, ignorez cet email.

L'équipe IFRI_MentorLink"""
    mail.send(msg)
    return lien

# ==========================================
#  AJOUT : FONCTION POUR LE MOT DE PASSE OUBLIÉ
# ==========================================
def send_reset_email(email, reset_link):
    """Envoie l'e-mail contenant le lien de réinitialisation du mot de passe"""
    msg = Message(
        subject="Réinitialisation de votre mot de passe - IFRI_MentorLink",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.body = f"""Bonjour,

Une demande de réinitialisation de mot de passe a été faite pour votre compte IFRI_MentorLink.

Cliquez sur le lien ci-dessous pour modifier votre mot de passe :
{reset_link}

Ce lien expire dans 1 heure.

Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet e-mail en toute sécurité.

L'équipe IFRI_MentorLink"""
    mail.send(msg)