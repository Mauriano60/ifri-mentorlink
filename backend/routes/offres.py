from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from db.database import fetch_all, fetch_one, execute
from services.matching_service import obtenir_suggestions_matching
from services.notification_service import creer_notification
from utils.responses import get_user_context
from utils.csrf import csrf_required

offres_bp = Blueprint('offres', __name__)


@offres_bp.route('/offres', methods=['GET', 'POST'])
@csrf_required
def offres():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    connecte_id = session['user_id']
    match_result = None
    confirmer_done = False
    page = request.args.get('page', 1, type=int)
    per_page = 12

    try:
        if request.method == 'POST':
            annonce_id = request.form.get('annonce_id')
            action = request.form.get('action', 'calculer')
            if annonce_id:
                annonce = fetch_one("SELECT * FROM offre_mentorat WHERE id = %s AND statut_offre = 1", (annonce_id,))
                if annonce and annonce['utilisateur_id'] != connecte_id:
                    if action == 'calculer':
                        match_result = {'annonce_id': int(annonce_id)}
                        suggestions = obtenir_suggestions_matching(connecte_id, role='mentee')
                        for sug in suggestions:
                            if sug['id'] == annonce['utilisateur_id']:
                                match_result.update(sug)
                                break
                        if not match_result.get('id'):
                            flash("Aucune compatibilité calculée pour cette offre.", "info")
                    elif action == 'confirmer':
                        existant = fetch_one("""
                            SELECT id FROM correspondances
                            WHERE ((mentor_id = %s AND mentee_id = %s) OR (mentor_id = %s AND mentee_id = %s))
                              AND statut_correspondance IN (0, 1)
                        """, (annonce['utilisateur_id'], connecte_id, connecte_id, annonce['utilisateur_id']))
                        if not existant:
                            score = float(request.form.get('score', 0))
                            correspondance_id = execute("""
                                INSERT INTO correspondances (mentor_id, mentee_id, score_compatibilite, statut_correspondance, initiateur_id)
                                VALUES (%s, %s, %s, 0, %s)
                            """, (annonce['utilisateur_id'], connecte_id, score, connecte_id))
                            if not correspondance_id:
                                recup = fetch_one("""
                                    SELECT id FROM correspondances
                                    WHERE mentor_id = %s AND mentee_id = %s AND initiateur_id = %s
                                    ORDER BY id DESC LIMIT 1
                                """, (annonce['utilisateur_id'], connecte_id, connecte_id))
                                id_match = recup['id'] if recup else None
                            else:
                                id_match = correspondance_id
                            nom_exp = f"{session.get('prenom', '')} {session.get('nom', '')}"
                            if id_match:
                                creer_notification(
                                    utilisateur_id=annonce['utilisateur_id'],
                                    message=f"{nom_exp} a besoin de votre aide !",
                                    type_notification="match_demande",
                                    correspondance_id=id_match
                                )
                            flash("Match effectué avec succès !", "success")
                            confirmer_done = True
                        else:
                            flash("Une demande est déjà en cours avec cette personne.", "info")

        total = fetch_one("""
            SELECT COUNT(*) as count FROM offre_mentorat o
            JOIN utilisateurs u ON u.id = o.utilisateur_id
            WHERE u.est_actif = 1 AND o.statut_offre = 1 AND o.utilisateur_id != %s
              AND NOT EXISTS (
                SELECT 1 FROM correspondances c
                WHERE ((c.mentor_id = o.utilisateur_id AND c.mentee_id = %s)
                    OR (c.mentor_id = %s AND c.mentee_id = o.utilisateur_id))
                  AND c.statut_correspondance IN (0, 1)
              )
        """, (connecte_id, connecte_id, connecte_id))
        total_pages = max(1, (total['count'] + per_page - 1) // per_page)
        page = min(page, total_pages)
        offset = (page - 1) * per_page

        offres_liste = fetch_all("""
            SELECT o.*, m.nom as matiere, u.prenom, u.nom as nom_user, u.avatar_url,
                   f.nom as filiere, n.nom as niveau,
                   c.statut_correspondance, c.initiateur_id, c.score_compatibilite as score_enregistre
            FROM offre_mentorat o
            JOIN matieres m ON m.id = o.matiere_id
            JOIN utilisateurs u ON u.id = o.utilisateur_id
            JOIN filieres_etudes f ON f.id = u.id_filiere
            JOIN niveaux_etudes n ON n.id = u.id_niveau
            LEFT JOIN correspondances c ON (
                (c.mentor_id = o.utilisateur_id AND c.mentee_id = %s)
                OR (c.mentor_id = %s AND c.mentee_id = o.utilisateur_id)
            )
            WHERE u.est_actif = 1 AND o.statut_offre = 1
              AND o.utilisateur_id != %s
              AND NOT EXISTS (
                SELECT 1 FROM correspondances c2
                WHERE ((c2.mentor_id = o.utilisateur_id AND c2.mentee_id = %s)
                    OR (c2.mentor_id = %s AND c2.mentee_id = o.utilisateur_id))
                  AND c2.statut_correspondance IN (0, 1)
              )
            ORDER BY o.cree_le DESC
            LIMIT %s OFFSET %s
        """, (connecte_id, connecte_id, connecte_id, connecte_id, connecte_id, per_page, offset))

        scores_profil = obtenir_suggestions_matching(connecte_id)
        scores_map = {s['id']: s['score_compatibilite'] for s in scores_profil}

        ids_offres = [o['utilisateur_id'] for o in offres_liste]
        if ids_offres:
            placeholders = ','.join(['%s'] * len(ids_offres))
            toutes_dispos = fetch_all(f"""
                SELECT utilisateur_id, jour_semaine, heure_debut, heure_fin
                FROM disponibilites
                WHERE utilisateur_id IN ({placeholders})
                ORDER BY FIELD(jour_semaine, 'Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi')
            """, ids_offres)
            dispos_map = {}
            for d in toutes_dispos:
                dispos_map.setdefault(d['utilisateur_id'], []).append(d)
        else:
            dispos_map = {}

        for offre in offres_liste:
            if offre['statut_correspondance'] is not None:
                offre['score_affiche'] = offre['score_enregistre']
            else:
                offre['score_affiche'] = scores_map.get(offre['utilisateur_id'], 0.00)
            offre['disponibilites'] = dispos_map.get(offre['utilisateur_id'], [])

        if confirmer_done:
            match_result = None

        matieres = fetch_all("SELECT id, nom FROM matieres ORDER BY nom")
        context = get_user_context()
        context['offres'] = offres_liste
        context['match_result'] = match_result
        context['page'] = page
        context['total_pages'] = total_pages
        context['matieres'] = matieres
        return render_template('mentorat/offres.html', **context)

    except Exception as e:
        return f"Erreur lors du chargement des offres: {str(e)}", 500


@offres_bp.route('/offres/creer', methods=['GET', 'POST'])
@csrf_required
def creer_offre():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    connecte_id = session['user_id']
    error = None
    matchs_trouves = None

    try:
        toutes_matieres = fetch_all("SELECT * FROM matieres")
        res_comp = fetch_all("SELECT matiere_id FROM competences_utilisateur WHERE utilisateur_id = %s", (connecte_id,))
        ids_comp = {r['matiere_id'] for r in res_comp}
        matieres = [m for m in toutes_matieres if m['id'] in ids_comp]
        user_dispos = fetch_all("""
            SELECT jour_semaine, heure_debut, heure_fin FROM disponibilites
            WHERE utilisateur_id = %s
            ORDER BY FIELD(jour_semaine, 'Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi')
        """, (connecte_id,))
    except Exception as e:
        matieres = []
        user_dispos = []
        error = f"Erreur lors du chargement des matières: {str(e)}"

    if request.method == 'POST':
        matiere_id = request.form.get('matiere_id')
        format_ = request.form.get('format')
        description = request.form.get('description', '').strip()
        jours = request.form.getlist('jour[]')
        heures_debut = request.form.getlist('heure_debut[]')
        heures_fin = request.form.getlist('heure_fin[]')
        formats_autorises = ['en_ligne', 'presentiel', 'les_deux']
        if not matiere_id or not format_:
            error = "Matière et format sont requis"
        elif format_ not in formats_autorises:
            error = "Format invalide (présentiel, visio ou hybride)"
        elif not description:
            error = "Description requise"
        elif len(description) > 1000:
            error = "Description trop longue (max 1000 caractères)"
        else:
            try:
                execute("""
                    INSERT INTO offre_mentorat (utilisateur_id, matiere_id, format, description, statut_offre)
                    VALUES (%s, %s, %s, %s, 1)
                """, (connecte_id, matiere_id, format_, description))

                execute("DELETE FROM disponibilites WHERE utilisateur_id = %s", (connecte_id,))
                for i, jour in enumerate(jours):
                    if jour and i < len(heures_debut) and i < len(heures_fin) and heures_debut[i] and heures_fin[i]:
                        execute("""
                            INSERT INTO disponibilites (utilisateur_id, jour_semaine, heure_debut, heure_fin)
                            VALUES (%s, %s, %s, %s)
                        """, (connecte_id, jour, heures_debut[i], heures_fin[i]))

                flash("Votre offre de mentorat a été publiée avec succès !", "success")

                nom_matiere = fetch_one("SELECT nom FROM matieres WHERE id = %s", (matiere_id,))['nom']
                toutes_suggestions = obtenir_suggestions_matching(connecte_id, role='mentor')
                toutes_suggestions.sort(key=lambda x: x['score_compatibilite'], reverse=True)
                matchs_trouves = [m for m in toutes_suggestions if m['score_compatibilite'] >= 50 and nom_matiere in m.get('commun_matieres', [])][:4]

            except Exception as e:
                error = f"Erreur lors de la création de l'offre et du matching instantané: {str(e)}"

    ctx = get_user_context()
    ctx.update({'matieres': matieres, 'error': error, 'matchs': matchs_trouves, 'user_dispos': user_dispos})
    return render_template('mentorat/creer-offre.html', **ctx)
