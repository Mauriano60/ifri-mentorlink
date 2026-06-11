from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from db.database import fetch_all, fetch_one, execute
from services.matching_service import obtenir_suggestions_matching
from services.notification_service import creer_notification
from utils.responses import get_user_context
from utils.csrf import csrf_required

demandes_bp = Blueprint('demandes', __name__)


@demandes_bp.route('/demandes', methods=['GET', 'POST'])
@csrf_required
def demandes():
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
                annonce = fetch_one("SELECT * FROM demande_mentorat WHERE id = %s AND statut_demande = 1", (annonce_id,))
                if annonce and annonce['utilisateur_id'] != connecte_id:
                    if action == 'calculer':
                        match_result = {'annonce_id': int(annonce_id)}
                        suggestions = obtenir_suggestions_matching(connecte_id, role='mentor')
                        for sug in suggestions:
                            if sug['id'] == annonce['utilisateur_id']:
                                match_result.update(sug)
                                break
                        if not match_result.get('id'):
                            flash("Aucune compatibilité calculée pour cette demande.", "info")
                    elif action == 'confirmer':
                        existant = fetch_one("""
                            SELECT id FROM correspondances
                            WHERE ((mentor_id = %s AND mentee_id = %s) OR (mentor_id = %s AND mentee_id = %s))
                              AND statut_correspondance IN (0, 1)
                        """, (connecte_id, annonce['utilisateur_id'], annonce['utilisateur_id'], connecte_id))
                        if not existant:
                            score = float(request.form.get('score', 0))
                            correspondance_id = execute("""
                                INSERT INTO correspondances (mentor_id, mentee_id, score_compatibilite, statut_correspondance, initiateur_id)
                                VALUES (%s, %s, %s, 0, %s)
                            """, (connecte_id, annonce['utilisateur_id'], score, connecte_id))
                            if not correspondance_id:
                                recup = fetch_one("""
                                    SELECT id FROM correspondances
                                    WHERE mentor_id = %s AND mentee_id = %s AND initiateur_id = %s
                                    ORDER BY id DESC LIMIT 1
                                """, (connecte_id, annonce['utilisateur_id'], connecte_id))
                                id_match = recup['id'] if recup else None
                            else:
                                id_match = correspondance_id
                            nom_exp = f"{session.get('prenom', '')} {session.get('nom', '')}"
                            if id_match:
                                creer_notification(
                                    utilisateur_id=annonce['utilisateur_id'],
                                    message=f"{nom_exp} vous propose son aide !",
                                    type_notification="match_demande",
                                    correspondance_id=id_match
                                )
                            flash("Match effectué avec succès !", "success")
                            confirmer_done = True
                        else:
                            flash("Une demande est déjà en cours avec cette personne.", "info")

        total = fetch_one("""
            SELECT COUNT(*) as count FROM demande_mentorat d
            JOIN utilisateurs u ON u.id = d.utilisateur_id
            WHERE u.est_actif = 1 AND d.statut_demande = 1 AND d.utilisateur_id != %s
              AND NOT EXISTS (
                SELECT 1 FROM correspondances c
                WHERE ((c.mentor_id = %s AND c.mentee_id = d.utilisateur_id)
                    OR (c.mentor_id = d.utilisateur_id AND c.mentee_id = %s))
                  AND c.statut_correspondance IN (0, 1)
              )
        """, (connecte_id, connecte_id, connecte_id))
        total_pages = max(1, (total['count'] + per_page - 1) // per_page)
        page = min(page, total_pages)
        offset = (page - 1) * per_page

        demandes_liste = fetch_all("""
            SELECT d.*, m.nom as matiere, u.prenom, u.nom as nom_user, u.avatar_url,
                   f.nom as filiere, n.nom as niveau,
                   c.statut_correspondance, c.initiateur_id, c.score_compatibilite as score_enregistre
            FROM demande_mentorat d
            JOIN matieres m ON m.id = d.matiere_id
            JOIN utilisateurs u ON u.id = d.utilisateur_id
            JOIN filieres_etudes f ON f.id = u.id_filiere
            JOIN niveaux_etudes n ON n.id = u.id_niveau
            LEFT JOIN correspondances c ON (
                (c.mentor_id = %s AND c.mentee_id = d.utilisateur_id)
                OR (c.mentor_id = d.utilisateur_id AND c.mentee_id = %s)
            )
            WHERE u.est_actif = 1 AND d.statut_demande = 1
              AND d.utilisateur_id != %s
              AND NOT EXISTS (
                SELECT 1 FROM correspondances c2
                WHERE ((c2.mentor_id = %s AND c2.mentee_id = d.utilisateur_id)
                    OR (c2.mentor_id = d.utilisateur_id AND c2.mentee_id = %s))
                  AND c2.statut_correspondance IN (0, 1)
              )
            ORDER BY d.cree_le DESC
            LIMIT %s OFFSET %s
        """, (connecte_id, connecte_id, connecte_id, connecte_id, connecte_id, per_page, offset))

        scores_profil = obtenir_suggestions_matching(connecte_id, role='mentor')
        scores_map = {s['id']: s['score_compatibilite'] for s in scores_profil}

        ids_demandes = [d['utilisateur_id'] for d in demandes_liste]
        if ids_demandes:
            placeholders = ','.join(['%s'] * len(ids_demandes))
            toutes_dispos = fetch_all(f"""
                SELECT utilisateur_id, jour_semaine, heure_debut, heure_fin
                FROM disponibilites
                WHERE utilisateur_id IN ({placeholders})
                ORDER BY FIELD(jour_semaine, 'Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi')
            """, ids_demandes)
            dispos_map = {}
            for d in toutes_dispos:
                dispos_map.setdefault(d['utilisateur_id'], []).append(d)
        else:
            dispos_map = {}

        for demande in demandes_liste:
            if demande['statut_correspondance'] is not None:
                demande['score_affiche'] = demande['score_enregistre']
            else:
                demande['score_affiche'] = scores_map.get(demande['utilisateur_id'], 0.00)
            demande['disponibilites'] = dispos_map.get(demande['utilisateur_id'], [])

        if confirmer_done:
            match_result = None

        matieres = fetch_all("SELECT id, nom FROM matieres ORDER BY nom")
        context = get_user_context()
        context['demandes'] = demandes_liste
        context['match_result'] = match_result
        context['page'] = page
        context['total_pages'] = total_pages
        context['matieres'] = matieres
        return render_template('mentorat/demandes.html', **context)

    except Exception as e:
        return f"Erreur lors du chargement des demandes: {str(e)}", 500


@demandes_bp.route('/demandes/creer', methods=['GET', 'POST'])
@csrf_required
def creer_demande():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    connecte_id = session['user_id']
    error = None
    matchs_trouves = None

    try:
        toutes_matieres = fetch_all("SELECT * FROM matieres")
        res_lac = fetch_all("SELECT matiere_id FROM difficultes_utilisateur WHERE utilisateur_id = %s", (connecte_id,))
        ids_lac = {r['matiere_id'] for r in res_lac}
        matieres = [m for m in toutes_matieres if m['id'] in ids_lac]
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
            error = "Format invalide (en_ligne, présentiel ou les_deux)"
        elif not description:
            error = "Description requise"
        elif len(description) > 1000:
            error = "Description trop longue (max 1000 caractères)"
        else:
            try:
                execute("""
                    INSERT INTO demande_mentorat (utilisateur_id, matiere_id, format, description, statut_demande)
                    VALUES (%s, %s, %s, %s, 1)
                """, (connecte_id, matiere_id, format_, description))

                execute("DELETE FROM disponibilites WHERE utilisateur_id = %s", (connecte_id,))
                for i, jour in enumerate(jours):
                    if jour and i < len(heures_debut) and i < len(heures_fin) and heures_debut[i] and heures_fin[i]:
                        execute("""
                            INSERT INTO disponibilites (utilisateur_id, jour_semaine, heure_debut, heure_fin)
                            VALUES (%s, %s, %s, %s)
                        """, (connecte_id, jour, heures_debut[i], heures_fin[i]))

                flash("Votre demande d'aide a été partagée avec succès !", "success")

                nom_matiere = fetch_one("SELECT nom FROM matieres WHERE id = %s", (matiere_id,))['nom']
                toutes_suggestions = obtenir_suggestions_matching(connecte_id)
                toutes_suggestions.sort(key=lambda x: x['score_compatibilite'], reverse=True)
                matchs_trouves = [m for m in toutes_suggestions if m['score_compatibilite'] >= 50 and nom_matiere in m.get('commun_matieres', [])][:4]

            except Exception as e:
                error = f"Erreur lors de la création de la demande et du matching instantané: {str(e)}"

    ctx = get_user_context()
    ctx.update({'matieres': matieres, 'error': error, 'matchs': matchs_trouves, 'user_dispos': user_dispos})
    return render_template('mentorat/creer-demande.html', **ctx)
