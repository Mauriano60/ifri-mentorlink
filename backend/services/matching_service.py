from db.database import fetch_all, fetch_one

def obtenir_suggestions_matching(utilisateur_id, role='mentee'):
    """
    Calcule les correspondances pour un utilisateur donné selon son rôle actuel.
    
    PARAMÈTRES :
    - utilisateur_id (int) : L'ID de l'étudiant connecté.
    - role (str) : 'mentee' (par défaut) ou 'mentor'.
      * Si 'mentee' : On cherche des MENTORS pour combler ses difficultés.
      * Si 'mentor' : On cherche des MENTEES à qui apporter son aide.
    """
    suggestions = []

    if not utilisateur_id or not isinstance(utilisateur_id, int):
        print("Erreur : utilisateur_id invalide")
        return []

    try:
        # 1. RÉCUPÉRATION DU PROFIL DE L'UTILISATEUR CONNECTÉ ──────────────
        user_connecte = fetch_one("""
            SELECT id, id_filiere, id_niveau
            FROM utilisateurs
            WHERE id = %s AND est_actif = 1
        """, (utilisateur_id,))

        if not user_connecte:
            print(f"Utilisateur {utilisateur_id} introuvable ou inactif")
            return []

        # 2. TRAITEMENT DES ANNONCES SELON LES DEUX CAS DE FIGURE ─────────
        mes_matieres = []
        
        if role == 'mentee':
            # CAS N°1 : Je suis Mentee -> Je récupère MES demandes actives (mes difficultés)
            res_demandes = fetch_all("""
                SELECT DISTINCT matiere_id FROM demande_mentorat 
                WHERE utilisateur_id = %s AND statut_demande = 1
            """, (utilisateur_id,))
            mes_matieres = [r['matiere_id'] for r in res_demandes]
            
        elif role == 'mentor':
            # CAS N°2 : Je suis Mentor -> Je récupère MES offres actives (mes compétences)
            res_offres = fetch_all("""
                SELECT DISTINCT matiere_id FROM offre_mentorat 
                WHERE utilisateur_id = %s AND statut_offre = 1
            """, (utilisateur_id,))
            mes_matieres = [r['matiere_id'] for r in res_offres]

        # 3. ISOLEMENT DES DISPONIBILITÉS RESTÉES LIBRES
        dispos_globales_user = fetch_all("""
            SELECT jour_semaine, heure_debut, heure_fin FROM disponibilites 
            WHERE utilisateur_id = %s
        """, (utilisateur_id,))
        
        dispos_occupees_user = fetch_all("""
            SELECT d.jour_semaine, d.heure_debut, d.heure_fin FROM disponibilites d
            JOIN correspondances c ON (c.mentee_id = d.utilisateur_id OR c.mentor_id = d.utilisateur_id)
            WHERE d.utilisateur_id = %s AND c.statut_correspondance = 1
        """, (utilisateur_id,))

        dispos_user = []
        for dg in dispos_globales_user:
            est_occupe = False
            for do in dispos_occupees_user:
                if dg['jour_semaine'] == do['jour_semaine'] and (dg['heure_debut'] < do['heure_fin'] and dg['heure_fin'] > do['heure_debut']):
                    est_occupe = True
                    break
            if not est_occupe:
                dispos_user.append(dg)

        # 4. CHARGEMENT OPTIMISÉ DES AUTRES COMPTES (LEFT JOIN)
        donnees_brutes = fetch_all("""
            SELECT u.id, u.prenom, u.nom, u.biographie, u.id_filiere, u.id_niveau,
                   f.nom as filiere, n.nom as niveau,
                   d.jour_semaine, d.heure_debut, d.heure_fin
            FROM utilisateurs u
            JOIN filieres_etudes f ON f.id = u.id_filiere
            JOIN niveaux_etudes n ON n.id = u.id_niveau
            LEFT JOIN disponibilites d ON d.utilisateur_id = u.id
            WHERE u.id != %s AND u.est_actif = 1
        """, (utilisateur_id,))

        utilisateurs_map = {}
        for ligne in donnees_brutes:
            uid = ligne['id']
            if uid not in utilisateurs_map:
                utilisateurs_map[uid] = {
                    'id': ligne['id'], 'prenom': ligne['prenom'], 'nom': ligne['nom'],
                    'biographie': ligne['biographie'], 'id_filiere': ligne['id_filiere'],
                    'id_niveau': ligne['id_niveau'], 'filiere': ligne['filiere'], 'niveau': ligne['niveau'],
                    'dispos_globales': []
                }
            if ligne['jour_semaine'] is not None:
                utilisateurs_map[uid]['dispos_globales'].append({
                    'jour_semaine': ligne['jour_semaine'],
                    'heure_debut': ligne['heure_debut'],
                    'heure_fin': ligne['heure_fin']
                })

        toutes_dispos_occupees = fetch_all("""
            SELECT d.utilisateur_id, d.jour_semaine, d.heure_debut, d.heure_fin 
            FROM disponibilites d
            JOIN correspondances c ON (c.mentee_id = d.utilisateur_id OR c.mentor_id = d.utilisateur_id)
            WHERE c.statut_correspondance = 1
        """)

        # 5. CALCUL DES SCORES DE COMPATIBILITÉ 
        for cible_id, cible in utilisateurs_map.items():

            # 5a. Évaluation des Annonces (40%) 
            nb_competences_match = 0
            
            if mes_matieres:
                placeholders = ','.join(['%s'] * len(mes_matieres))
                
                if role == 'mentee':
                    # CAS 1 : Je cherche des Mentors -> Est-ce que la cible offre ce dont j'ai besoin ?
                    check_table = fetch_one(f"""
                        SELECT COUNT(DISTINCT matiere_id) as count FROM offre_mentorat 
                        WHERE utilisateur_id = %s AND statut_offre = 1 AND matiere_id IN ({placeholders})
                    """, (cible['id'], *mes_matieres))
                else:
                    # CAS 2 : Je cherche des Mentees -> Est-ce que la cible demande ce que je maîtrise ?
                    check_table = fetch_one(f"""
                        SELECT COUNT(DISTINCT matiere_id) as count FROM demande_mentorat 
                        WHERE utilisateur_id = %s AND statut_demande = 1 AND matiere_id IN ({placeholders})
                    """, (cible['id'], *mes_matieres))
                    
                nb_competences_match = check_table['count'] if check_table else 0

            # Application de la pondération (Gestion propre du Cold Start)
            total_matieres_references = max(1, len(mes_matieres))
            if len(mes_matieres) > 0 and nb_competences_match > 0:
                score_competences = (nb_competences_match / total_matieres_references) * 40
            else:
                score_competences = 15.00  # Score neutre si pas d'annonces en commun

            # 5b. Évaluation de l'Emploi du Temps (30%) 
            occupees_cible = [d for d in toutes_dispos_occupees if d['utilisateur_id'] == cible['id']]
            
            dispos_libres_cible = []
            for dg in cible['dispos_globales']:
                est_occupe = False
                for do in occupees_cible:
                    if dg['jour_semaine'] == do['jour_semaine'] and (dg['heure_debut'] < do['heure_fin'] and dg['heure_fin'] > do['heure_debut']):
                        est_occupe = True
                        break
                if not est_occupe:
                    dispos_libres_cible.append(dg)

            creneaux_compatibles = 0
            for d_user in dispos_user:
                for d_cible in dispos_libres_cible:
                    if d_user['jour_semaine'] == d_cible['jour_semaine'] and (d_user['heure_debut'] < d_cible['heure_fin'] and d_user['heure_fin'] > d_cible['heure_debut']):
                        creneaux_compatibles += 1

            if len(dispos_user) == 0:
                score_dispos = 15.00
            else:
                score_dispos = min((creneaux_compatibles / len(dispos_user)) * 30, 30.00)

            #  5c. Évaluation de l'Affinité de Filière (20%) 
            score_filiere = 20.00 if cible['id_filiere'] == user_connecte['id_filiere'] else 10.00

            #  5d. Évaluation de la Proximité de Promotion (10%) 
            difference_niveau = abs(cible['id_niveau'] - user_connecte['id_niveau'])

            if difference_niveau == 1:
                score_niveau = 10.00
            elif difference_niveau == 0:
                score_niveau = 8.00
            elif difference_niveau == 2:
                score_niveau = 5.00
            else:
                score_niveau = 3.00
            

            #  5e. CONSOLIDATION DU SCORE FINAL 
            score_total = round(score_competences + score_dispos + score_filiere + score_niveau, 2)
            score_total = max(0.00, min(100.00, score_total))

            #  6. EXCLUSION DES DOUBLONS VALIDÉS 
            deja_valide = fetch_one("""
                SELECT id FROM correspondances
                WHERE ((mentor_id = %s AND mentee_id = %s) OR (mentor_id = %s AND mentee_id = %s))
                AND statut_correspondance = 1
            """, (utilisateur_id, cible['id'], cible['id'], utilisateur_id))

            if not deja_valide:
                avatar = fetch_one("SELECT avatar_url FROM utilisateurs WHERE id = %s", (cible['id'],))
                avatar_url = avatar['avatar_url'] if avatar else None

                commun_matieres = []
                if mes_matieres:
                    placeholders = ','.join(['%s'] * len(mes_matieres))
                    if role == 'mentee':
                        rows = fetch_all(f"""
                            SELECT DISTINCT m.nom FROM offre_mentorat o
                            JOIN matieres m ON m.id = o.matiere_id
                            WHERE o.utilisateur_id = %s AND o.statut_offre = 1 AND o.matiere_id IN ({placeholders})
                        """, (cible['id'], *mes_matieres))
                    else:
                        rows = fetch_all(f"""
                            SELECT DISTINCT m.nom FROM demande_mentorat d
                            JOIN matieres m ON m.id = d.matiere_id
                            WHERE d.utilisateur_id = %s AND d.statut_demande = 1 AND d.matiere_id IN ({placeholders})
                        """, (cible['id'], *mes_matieres))
                    commun_matieres = [r['nom'] for r in rows]

                commun_dispos = []
                for d_user in dispos_user:
                    for d_cible in dispos_libres_cible:
                        if d_user['jour_semaine'] == d_cible['jour_semaine'] and (d_user['heure_debut'] < d_cible['heure_fin'] and d_user['heure_fin'] > d_cible['heure_debut']):
                            commun_dispos.append({'jour_semaine': d_cible['jour_semaine'], 'heure_debut': d_cible['heure_debut'], 'heure_fin': d_cible['heure_fin']})
                            break

                suggestions.append({
                    'id': cible['id'],
                    'prenom': cible['prenom'],
                    'nom': cible['nom'],
                    'biographie': cible['biographie'],
                    'avatar_url': avatar_url,
                    'filiere': cible['filiere'],
                    'niveau': cible['niveau'],
                    'score_compatibilite': score_total,
                    'commun_matieres': commun_matieres,
                    'commun_dispos': commun_dispos
                })

        print(f"Moteur de matching exécuté avec succès [Rôle: {role}] pour l'utilisateur {utilisateur_id}")

    except Exception as e:
        print(f"Erreur système au cours du calcul du matching : {str(e)}")
        
    return suggestions