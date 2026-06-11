from flask import Blueprint, render_template, session, redirect, url_for
from db.database import fetch_all

references_bp = Blueprint('references', __name__)

@references_bp.route('/references')
def references():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    try:
        # Récupération propre de toutes les données de référence triées par nom
        matieres = fetch_all("SELECT * FROM matieres ORDER BY nom")
        filieres = fetch_all("SELECT * FROM filieres_etudes ORDER BY nom")
        niveaux = fetch_all("SELECT * FROM niveaux_etudes ORDER BY nom")
        
        return render_template('references/index.html',
                               matieres=matieres,
                               filieres=filieres,
                               niveaux=niveaux)
                               
    except Exception as e:
        return f"Erreur lors du chargement des références: {str(e)}", 500