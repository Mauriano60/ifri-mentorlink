/* ============================================================
   script.js — Logique de validation et de navigation
   Page d'inscription IFRI_MentorLink – Étape 1
   ============================================================ */

/**
 * Fonction principale de validation de l'étape 1.
 * Appelée au clic sur le bouton "Suivant →".
 * Vérifie tous les champs et affiche les erreurs éventuelles.
 */
function validerEtape1() {

  /* === Récupération des champs du formulaire === */

  // Champ Nom
  const nom = document.getElementById('nom');

  // Champ Prénom
  const prenom = document.getElementById('prenom');

  // Champ Email
  const email = document.getElementById('email');

  // Champ Téléphone
  const telephone = document.getElementById('telephone');

  // Champ Mot de passe
  const motdepasse = document.getElementById('motdepasse');

  // Champ Confirmer le mot de passe
  const confirmer = document.getElementById('confirmer');

  /* === Réinitialisation des états d'erreur === */
  // On retire les classes d'erreur précédentes avant de re-valider
  [nom, prenom, email, telephone, motdepasse, confirmer].forEach(function(champ) {
    champ.classList.remove('is-invalid'); // Supprime la bordure rouge Bootstrap
    champ.classList.remove('is-valid');   // Supprime la bordure verte Bootstrap
  });

  /* === Indicateur global : le formulaire est-il valide ? === */
  let formulaireValide = true; // On suppose que tout est correct au départ

  /* -------------------------------------------------------
     Validation du champ NOM
     Règle : ne doit pas être vide
  ------------------------------------------------------- */
  if (nom.value.trim() === '') {
    // Le champ est vide : on signale l'erreur
    nom.classList.add('is-invalid'); // Bordure rouge Bootstrap
    formulaireValide = false;        // Le formulaire n'est plus valide
  } else {
    nom.classList.add('is-valid'); // Bordure verte si OK
  }

  /* -------------------------------------------------------
     Validation du champ PRÉNOM
     Règle : ne doit pas être vide
  ------------------------------------------------------- */
  if (prenom.value.trim() === '') {
    prenom.classList.add('is-invalid'); // Signale l'erreur
    formulaireValide = false;
  } else {
    prenom.classList.add('is-valid'); // Valide
  }

  /* -------------------------------------------------------
     Validation du champ EMAIL
     Règle : format email valide (contient @ et .)
  ------------------------------------------------------- */
  const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  // Expression régulière simple pour valider le format email

  if (!regexEmail.test(email.value.trim())) {
    // L'email ne correspond pas au format attendu
    email.classList.add('is-invalid');
    formulaireValide = false;
  } else {
    email.classList.add('is-valid');
  }

  /* -------------------------------------------------------
     Validation du champ TÉLÉPHONE
     Règle : ne doit pas être vide, format numérique attendu
  ------------------------------------------------------- */
  if (telephone.value.trim() === '') {
    // Champ vide
    telephone.classList.add('is-invalid');
    formulaireValide = false;
  } else {
    telephone.classList.add('is-valid');
  }

  /* -------------------------------------------------------
     Validation du MOT DE PASSE
     Règle : minimum 8 caractères
  ------------------------------------------------------- */
  if (motdepasse.value.length < 8) {
    // Mot de passe trop court
    motdepasse.classList.add('is-invalid');
    formulaireValide = false;
  } else {
    motdepasse.classList.add('is-valid');
  }

  /* -------------------------------------------------------
     Validation de la CONFIRMATION du mot de passe
     Règle : doit être identique au mot de passe saisi
  ------------------------------------------------------- */
  if (confirmer.value !== motdepasse.value || confirmer.value === '') {
    // Les mots de passe ne correspondent pas
    confirmer.classList.add('is-invalid');
    formulaireValide = false;
  } else {
    confirmer.classList.add('is-valid');
  }

  /* -------------------------------------------------------
     Si tout est valide : passage à l'étape suivante
  ------------------------------------------------------- */
  if (formulaireValide) {
    // Toutes les validations sont passées avec succès
    passerEtapeSuivante(); // On appelle la fonction de navigation
  }
  // Sinon, les erreurs sont affichées via les classes Bootstrap
}

/* ============================================================
   Fonction de navigation vers l'étape 2
   ============================================================ */

/**
 * Simule le passage à l'étape 2 du formulaire.
 * Dans une vraie application, cette fonction chargerait
 * le formulaire de l'étape 2 ou redirigerait vers une autre page.
 */
function passerEtapeSuivante() {

  // ---- Mise à jour visuelle du stepper ----

  // Marquer l'étape 1 comme complétée (cercle + libellé)
  const cercleEtape1 = document.querySelectorAll('.step-circle')[0];
  // Sélectionne le premier cercle du stepper

  cercleEtape1.classList.remove('active');    // Retire l'état actif (bleu rempli)
  cercleEtape1.classList.add('completed');    // Ajoute l'état complété

  // Activer l'étape 2 (rendre son cercle bleu)
  const cercleEtape2 = document.querySelectorAll('.step-circle')[1];
  // Sélectionne le deuxième cercle du stepper

  cercleEtape2.classList.add('active');       // Le rend bleu et actif

  // Mettre en gras le libellé de l'étape 2
  const labelEtape2 = document.querySelectorAll('.step-label')[1];
  labelEtape2.classList.remove('text-muted'); // Retire le gris
  labelEtape2.classList.add('fw-bold');       // Ajoute le gras

  // Retirer le gras du libellé de l'étape 1
  const labelEtape1 = document.querySelectorAll('.step-label')[0];
  labelEtape1.classList.remove('fw-bold');    // Retire le gras de l'étape 1
  labelEtape1.classList.add('text-muted');    // Le passe en gris

  // ---- Afficher une notification de succès à l'utilisateur ----
  afficherNotification('Étape 1 validée ! Passage au Profil académique...', 'success');

  // ---- Simulation d'une redirection après 1.5 secondes ----
  setTimeout(function() {
    // Dans une vraie application, on redirigerait ici vers la page d'étape 2
    // Exemple : window.location.href = 'etape2.html';
    console.log('Navigation vers l\'étape 2 : Profil académique');
    // Pour la démo, on réinitialise les bordures vertes après navigation simulée
    reinitialiserChamps();
  }, 1500); // Délai de 1,5 seconde avant la "navigation"
}

/* ============================================================
   Fonction d'affichage d'une notification temporaire
   ============================================================ */

/**
 * Affiche un message de notification Bootstrap en haut de la carte.
 * @param {string} message - Le texte à afficher
 * @param {string} type - Le type Bootstrap ('success', 'danger', 'info')
 */
function afficherNotification(message, type) {

  // Supprime une éventuelle notification précédente
  const ancienneNotif = document.getElementById('notifAlert');
  if (ancienneNotif) {
    ancienneNotif.remove(); // Supprime l'ancien élément du DOM
  }

  // Crée un nouvel élément d'alerte Bootstrap
  const alerte = document.createElement('div');
  alerte.id = 'notifAlert'; // Identifiant pour le retrouver plus tard

  // Classes Bootstrap pour l'alerte (type = success/danger/info)
  alerte.className = `alert alert-${type} alert-dismissible fade show mb-3`;
  alerte.setAttribute('role', 'alert'); // Accessibilité

  // Contenu de l'alerte : message + bouton de fermeture
  alerte.innerHTML = `
    <span>${message}</span>
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
  `;

  // Insère l'alerte au début de la carte formulaire
  const formCard = document.querySelector('.form-card');
  formCard.insertBefore(alerte, formCard.firstChild);
  // firstChild : insère avant le premier enfant de la carte
}

/* ============================================================
   Fonction de réinitialisation des états visuels des champs
   ============================================================ */

/**
 * Retire les classes de validation (is-valid, is-invalid)
 * de tous les champs du formulaire.
 */
function reinitialiserChamps() {

  // Liste de tous les ids de champs
  const ids = ['nom', 'prenom', 'email', 'telephone', 'motdepasse', 'confirmer'];

  // Boucle sur chaque champ pour retirer les classes visuelles
  ids.forEach(function(id) {
    const champ = document.getElementById(id); // Récupère l'élément
    if (champ) {
      champ.classList.remove('is-valid');   // Retire la bordure verte
      champ.classList.remove('is-invalid'); // Retire la bordure rouge
    }
  });
}

/* ============================================================
   Validation en temps réel (live) lors de la frappe
   Améliore l'UX : les erreurs disparaissent dès que l'utilisateur corrige
   ============================================================ */

// Attend que le DOM soit entièrement chargé avant d'attacher les événements
document.addEventListener('DOMContentLoaded', function() {

  // Liste des champs à surveiller en temps réel
  const champs = ['nom', 'prenom', 'email', 'telephone', 'motdepasse', 'confirmer'];

  champs.forEach(function(id) {
    const champ = document.getElementById(id); // Référence au champ

    if (champ) {
      // Événement 'input' : déclenché à chaque frappe de touche
      champ.addEventListener('input', function() {

        // Si le champ n'est plus vide, retire l'état d'erreur
        if (champ.value.trim() !== '') {
          champ.classList.remove('is-invalid'); // Retire la bordure rouge
        }
      });
    }
  });

  console.log('IFRI_MentorLink — Script de validation chargé avec succès.');
  // Message de confirmation dans la console du navigateur
});
