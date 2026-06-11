from functools import wraps
from flask import redirect, url_for, session

def login_required(f):
    """
    Décorateur de sécurité pour restreindre l'accès aux utilisateurs connectés.
    Redirige vers la page de connexion si 'user_id' n'est pas en session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function