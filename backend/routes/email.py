from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from db.database import fetch_one, execute
from services.mail_service import send_reset_email, generate_token, verify_token
from utils.csrf import csrf_required
import bcrypt

email_bp = Blueprint('email_bp', __name__)


@email_bp.route('/mot-de-passe-oublie', methods=['GET', 'POST'])
@csrf_required
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        user = fetch_one("SELECT id, email, prenom FROM utilisateurs WHERE email=%s AND est_actif=1", (email,))

        if user:
            token = generate_token(email, salt_type='password-reset')
            reset_link = url_for('email_bp.reset_password', token=token, _external=True)
            send_reset_email(email, reset_link)

            if current_app.config.get('MAIL_SUPPRESS_SEND'):
                return render_template('forgot_password.html', reset_link=reset_link, email_sent=True)

        flash("Un email de réinitialisation vous a été envoyé.", "success")
        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')


@email_bp.route('/reinitialiser-mot-de-passe/<token>', methods=['GET', 'POST'])
@csrf_required
def reset_password(token):
    email = verify_token(token, salt_type='password-reset', expiration=3600)
    if not email:
        flash("Lien invalide ou expiré.", "error")
        return redirect(url_for('email_bp.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('mot_de_passe', '')
        confirm = request.form.get('confirm_mot_de_passe', '')

        if password != confirm:
            flash("Mots de passe différents.", "error")
            return redirect(url_for('email_bp.reset_password', token=token))

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        execute(
            "UPDATE utilisateurs SET mot_de_passe=%s WHERE email=%s AND est_actif=1",
            (hashed, email)
        )

        flash("Mot de passe mis à jour avec succès.", "success")
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)
