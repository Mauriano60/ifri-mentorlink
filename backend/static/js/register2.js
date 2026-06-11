/* ============================================================
   script2.js — Logique de l'étape 2 : Profil académique
   Gère : sélection/désélection des badges, validation, navigation
   ============================================================ */

/* ============================================================
   INITIALISATION AU CHARGEMENT DU DOM
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
  /* Attend que tout le HTML soit prêt avant d'attacher les événements */

  /* --- Initialisation des badges cliquables --- */
  initialiserBadges('competences'); /* Groupe des compétences maîtrisées */
  initialiserBadges('lacunes');     /* Groupe des lacunes / besoins */

  /* --- Colorisation dynamique des selects --- */
  initialiserSelects();

  console.log('IFRI_MentorLink — Étape 2 chargée avec succès.');
});

/* ============================================================
   GESTION DES BADGES CLIQUABLES
   ============================================================ */

/**
 * Attache un écouteur de clic à chaque badge d'un groupe donné.
 * Au clic : bascule la classe "selected" (sélectionné ↔ désélectionné).
 *
 * @param {string} groupeId - L'id du conteneur parent des badges
 */
function initialiserBadges(groupeId) {

  /* Récupère le conteneur du groupe de badges */
  const conteneur = document.getElementById(groupeId);

  /* Vérifie que le conteneur existe bien dans le DOM */
  if (!conteneur) return;

  /* Sélectionne tous les éléments avec la classe "badge-pill" dans ce conteneur */
  const badges = conteneur.querySelectorAll('.badge-pill');

  /* Boucle sur chaque badge pour lui attacher un événement clic */
  badges.forEach(function (badge) {

    badge.addEventListener('click', function () {
      /* Au clic : bascule la classe "selected" */

      if (badge.classList.contains('selected')) {
        /* Si le badge est déjà sélectionné → on le désélectionne */
        badge.classList.remove('selected');

        /* Log pour debug : badge désélectionné */
        console.log(`[${groupeId}] Désélectionné : ${badge.dataset.valeur}`);

      } else {
        /* Si le badge n'est pas sélectionné → on le sélectionne */
        badge.classList.add('selected');

        /* Log pour debug : badge sélectionné */
        console.log(`[${groupeId}] Sélectionné : ${badge.dataset.valeur}`);
      }
    });
  });
}

/**
 * Récupère la liste des valeurs des badges sélectionnés dans un groupe.
 *
 * @param {string} groupeId - L'id du conteneur parent
 * @returns {Array<string>} - Tableau des valeurs sélectionnées
 */
function getSelectionnes(groupeId) {

  /* Récupère le conteneur du groupe */
  const conteneur = document.getElementById(groupeId);

  /* Sélectionne tous les badges ayant la classe "selected" */
  const selectionnes = conteneur.querySelectorAll('.badge-pill.selected');

  /* Convertit en tableau et extrait l'attribut data-valeur de chacun */
  return Array.from(selectionnes).map(function (badge) {
    return badge.dataset.valeur; /* Retourne la valeur de l'attribut data-valeur */
  });
}

/* ============================================================
   GESTION DES SELECTS (Filière et Niveau)
   ============================================================ */

/**
 * Attache des événements aux selects pour :
 * - changer la couleur du texte quand une valeur est sélectionnée
 * - retirer les erreurs visuelles dès qu'une option est choisie
 */
function initialiserSelects() {

  /* Récupère les deux selects */
  const filiere = document.getElementById('filiere');
  const niveau  = document.getElementById('niveau');

  /* Applique la logique sur chaque select */
  [filiere, niveau].forEach(function (select) {

    select.addEventListener('change', function () {
      /* Au changement de valeur : */

      if (select.value !== '') {
        /* Une option valide est choisie → texte foncé */
        select.classList.add('selected-value');     /* Texte foncé */
        select.classList.remove('is-invalid');      /* Retire l'erreur rouge */
        select.classList.add('is-valid');           /* Ajoute le vert Bootstrap */
      }
    });
  });
}

/* ============================================================
   VALIDATION DE L'ÉTAPE 2
   Appelée au clic sur le bouton "Suivant →"
   ============================================================ */

/**
 * Valide les champs obligatoires de l'étape 2 :
 * - Filière (obligatoire)
 * - Niveau (obligatoire)
 * - Compétences (au moins 1 obligatoire)
 * - Lacunes (au moins 1 obligatoire)
 */
function validerEtape2() {

  /* === Récupération des éléments === */

  const filiere = document.getElementById('filiere'); /* Select Filière */
  const niveau  = document.getElementById('niveau');  /* Select Niveau */

  /* === Réinitialisation des états d'erreur === */
  filiere.classList.remove('is-invalid', 'is-valid'); /* Retire les états précédents */
  niveau.classList.remove('is-invalid', 'is-valid');  /* Idem pour niveau */

  /* === Indicateur global de validité === */
  let formulaireValide = true; /* On suppose que tout est correct au départ */

  /* -------------------------------------------------------
     Validation de la FILIÈRE
     Règle : une option doit être sélectionnée
  ------------------------------------------------------- */
  if (filiere.value === '') {
    /* Aucune filière choisie → erreur */
    filiere.classList.add('is-invalid');
    formulaireValide = false;
  } else {
    filiere.classList.add('is-valid'); /* Valide */
  }

  /* -------------------------------------------------------
     Validation du NIVEAU
     Règle : une option doit être sélectionnée
  ------------------------------------------------------- */
  if (niveau.value === '') {
    /* Aucun niveau choisi → erreur */
    niveau.classList.add('is-invalid');
    formulaireValide = false;
  } else {
    niveau.classList.add('is-valid'); /* Valide */
  }

  /* -------------------------------------------------------
     Validation des COMPÉTENCES
     Règle : au moins 1 badge doit être sélectionné
  ------------------------------------------------------- */
  const competencesSelectionnees = getSelectionnes('competences');
  /* Récupère le tableau des compétences sélectionnées */

  if (competencesSelectionnees.length === 0) {
    /* Aucune compétence choisie → erreur */
    afficherErreurBadges('competences', 'Veuillez sélectionner au moins une compétence.');
    formulaireValide = false;
  } else {
    /* OK : retire le message d'erreur s'il existe */
    retirerErreurBadges('competences');
  }

  /* -------------------------------------------------------
     Validation des LACUNES
     Règle : au moins 1 badge doit être sélectionné
  ------------------------------------------------------- */
  const lacunesSelectionnees = getSelectionnes('lacunes');
  /* Récupère le tableau des lacunes sélectionnées */

  if (lacunesSelectionnees.length === 0) {
    /* Aucune lacune choisie → erreur */
    afficherErreurBadges('lacunes', 'Veuillez sélectionner au moins un besoin académique.');
    formulaireValide = false;
  } else {
    /* OK : retire le message d'erreur */
    retirerErreurBadges('lacunes');
  }

  /* -------------------------------------------------------
     Si tout est valide : passage à l'étape suivante
  ------------------------------------------------------- */
  if (formulaireValide) {

    /* Prépare l'objet avec les données collectées (pour transmission future) */
    const donneesEtape2 = {
      filiere: filiere.value,                    /* Valeur de la filière */
      niveau: niveau.value,                      /* Valeur du niveau */
      competences: competencesSelectionnees,     /* Tableau des compétences */
      lacunes: lacunesSelectionnees              /* Tableau des lacunes */
    };

    /* Log des données collectées dans la console du navigateur */
    console.log('Données étape 2 :', donneesEtape2);

    /* Affiche une notification de succès avant navigation */
    afficherNotification('Étape 2 validée ! Passage aux Disponibilités...', 'success');

    /* Simulation de passage à l'étape 3 après 1.5 seconde */
    setTimeout(function () {
      /* Dans une vraie application : window.location.href = 'etape3.html'; */
      console.log('Navigation vers l\'étape 3 : Disponibilités');
    }, 1500);
  }
}

/* ============================================================
   GESTION DES ERREURS SUR LES GROUPES DE BADGES
   ============================================================ */

/**
 * Affiche un message d'erreur sous un groupe de badges.
 *
 * @param {string} groupeId - L'id du conteneur parent
 * @param {string} message  - Le message d'erreur à afficher
 */
function afficherErreurBadges(groupeId, message) {

  /* Vérifie si un message d'erreur existe déjà pour ce groupe */
  const existant = document.getElementById(`erreur-${groupeId}`);

  /* Évite de créer deux fois le même message */
  if (existant) return;

  /* Crée un élément paragraphe pour le message d'erreur */
  const erreur = document.createElement('p');
  erreur.id = `erreur-${groupeId}`;              /* ID unique pour le retrouver */
  erreur.className = 'text-danger small mt-1';   /* Style Bootstrap : rouge, petite police */
  erreur.textContent = message;                  /* Texte du message */

  /* Insère le message après le conteneur de badges */
  const conteneur = document.getElementById(groupeId);
  conteneur.insertAdjacentElement('afterend', erreur);
  /* insertAdjacentElement('afterend') : insère juste après l'élément cible */
}

/**
 * Retire le message d'erreur d'un groupe de badges.
 *
 * @param {string} groupeId - L'id du conteneur parent
 */
function retirerErreurBadges(groupeId) {

  /* Cherche le message d'erreur par son ID */
  const erreur = document.getElementById(`erreur-${groupeId}`);

  /* S'il existe, le supprime du DOM */
  if (erreur) erreur.remove();
}

/* ============================================================
   NOTIFICATION TEMPORAIRE (réutilisée de l'étape 1)
   ============================================================ */

/**
 * Affiche une alerte Bootstrap en haut de la carte formulaire.
 *
 * @param {string} message - Texte à afficher
 * @param {string} type    - Type Bootstrap ('success', 'danger', 'info')
 */
function afficherNotification(message, type) {

  /* Récupère la zone d'alerte dédiée dans le HTML */
  const zone = document.getElementById('zoneAlerte');

  /* Vide la zone d'une éventuelle alerte précédente */
  zone.innerHTML = '';

  /* Crée le contenu de l'alerte Bootstrap avec bouton de fermeture */
  zone.innerHTML = `
    <div class="alert alert-${type} alert-dismissible fade show mb-3" role="alert">
      <span>${message}</span>
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
    </div>
  `;
  /* Le data-bs-dismiss="alert" permet à Bootstrap de fermer l'alerte au clic sur la croix */
}

/* ============================================================
   NAVIGATION : RETOUR À L'ÉTAPE 1
   ============================================================ */

/**
 * Retourne à la page de l'étape 1.
 * Dans une vraie application, redirige vers index.html.
 */
function retourEtape1() {

  /* Redirection vers la page de l'étape 1 */
  /* window.location.href = 'index.html'; */

  /* Pour la démo : affiche une notification */
  afficherNotification('Retour à l\'étape 1 : Informations personnelles.', 'info');

  console.log('Retour vers l\'étape 1 : Informations personnelles');
}
