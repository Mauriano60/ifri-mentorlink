/* =========================================================
   IFRI_MentorLink — script.js
   Gestion des interactions de la page de connexion
   ========================================================= */

/* On attend que tout le HTML soit chargé avant d'exécuter le script
   'DOMContentLoaded' se déclenche quand le DOM est prêt (sans attendre images/CSS) */
document.addEventListener('DOMContentLoaded', function () {

  /* ── Récupération des éléments du DOM ──────────────── */

  var emailInput = document.getElementById('email');
  /* Champ de saisie de l'email ou du téléphone */

  var pwInput = document.getElementById('password');
  /* Champ de saisie du mot de passe */

  var eyeSvg = document.getElementById('eye-svg');
  /* Élément SVG de l'icône œil (son innerHTML sera modifié dynamiquement) */

  var btnLogin = document.getElementById('btnLogin');
  /* Bouton principal "Se connecter" */

  var errEmail = document.getElementById('err-email');
  /* Zone d'affichage du message d'erreur sous le champ email */

  var errPw = document.getElementById('err-pw');
  /* Zone d'affichage du message d'erreur sous le champ mot de passe */


  /* ── Effacer l'erreur email dès que l'utilisateur retape ── */

  /* Écoute les modifications du champ email */
  if (emailInput) {
    emailInput.addEventListener('input', function () {

      emailInput.classList.remove('error');
      /* Supprime la classe CSS 'error' qui rend la bordure rouge */

      errEmail.textContent = '';
      /* Vide le message d'erreur affiché sous le champ */
    });
  }

  /* ── Validation et soumission du formulaire ──────── */

  /* Vérifie que le bouton de connexion existe avant d'ajouter l'écouteur */
  if (btnLogin) {

    /* Écoute le clic sur le bouton "Se connecter" */
    btnLogin.addEventListener('click', function () {

      var email = emailInput ? emailInput.value.trim() : '';
      /* Récupère la valeur du champ email en supprimant les espaces en début/fin
         .trim() évite qu'un simple espace soit considéré comme une saisie valide */

      var password = pwInput ? pwInput.value.trim() : '';
      /* Récupère la valeur du champ mot de passe nettoyée */

      var ok = true;
      /* Variable booléenne qui deviendra false si une validation échoue */

      /* Réinitialisation de tous les états d'erreur avant de revalider */
      emailInput.classList.remove('error');  /* Retire la bordure rouge du champ email */
      pwInput.classList.remove('error');     /* Retire la bordure rouge du champ mot de passe */
      errEmail.textContent = '';             /* Efface le message d'erreur email */
      errPw.textContent    = '';            /* Efface le message d'erreur mot de passe */

      /* Validation du champ email : vérifie qu'il n'est pas vide */
      if (!email) {
        emailInput.classList.add('error');
        /* Ajoute la classe 'error' → la bordure devient rouge (défini dans style.css) */

        errEmail.textContent = 'Veuillez saisir votre email ou téléphone.';
        /* Affiche le message d'erreur sous le champ */

        ok = false;
        /* Marque la validation comme échouée */
      }

      /* Validation du champ mot de passe : vérifie qu'il n'est pas vide */
      if (!password) {
        pwInput.classList.add('error');
        /* Ajoute la classe 'error' → la bordure devient rouge */

        errPw.textContent = 'Veuillez saisir votre mot de passe.';
        /* Affiche le message d'erreur sous le champ */

        ok = false;
        /* Marque la validation comme échouée */
      }

      /* Si une validation a échoué, on arrête ici sans envoyer les données */
      if (!ok) return;

      /* ── Simulation d'un appel API de connexion ──── */
      /* En production, cette partie serait remplacée par un vrai fetch() vers un serveur */

      btnLogin.disabled = true;
      /* Désactive le bouton pour éviter les clics multiples pendant le chargement */

      btnLogin.textContent = 'Connexion en cours…';
      /* Informe l'utilisateur que la connexion est en cours */

      /* Simule un délai de réponse serveur de 1800 millisecondes (1,8 secondes) */
      setTimeout(function () {

        btnLogin.disabled = false;
        /* Réactive le bouton après la réponse (simulée) */

        btnLogin.textContent = 'Se connecter';
        /* Restaure le texte original du bouton */

        alert('Connexion simulée avec succès !');
        /* Affiche une alerte de confirmation (à remplacer par une redirection réelle) */

      }, 1800);
      /* Fin du setTimeout */

    });
    /* Fin de l'écouteur du clic sur btnLogin */

    /* Permet de soumettre le formulaire en appuyant sur la touche Entrée */
    document.addEventListener('keydown', function (e) {

      if (e.key === 'Enter') btnLogin.click();
      /* Si la touche Entrée est pressée, déclenche un clic programmatique sur le bouton */
    });

  }
  /* Fin du bloc gestion du bouton de connexion */

  /* ── Animation flottante des nœuds SVG ───────────── */

  /* Crée dynamiquement un élément <style> pour injecter les keyframes CSS
     Cette approche permet de définir les animations via JavaScript */
  var style = document.createElement('style');
  /* Crée un nouvel élément <style> HTML */

  style.textContent =
    /* Animation A : flottement léger vers le haut et la droite */
    '@keyframes floatA { 0%,100%{transform:translate(0,0)} 50%{transform:translate(3px,-6px)} }' +

    /* Animation B : flottement vers le haut et la gauche (direction opposée à A) */
    '@keyframes floatB { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-4px,-5px)} }' +

    /* Animation C : flottement vers le bas et la droite (direction différente) */
    '@keyframes floatC { 0%,100%{transform:translate(0,0)} 50%{transform:translate(5px,4px)} }';

  document.head.appendChild(style);
  /* Injecte les keyframes dans le <head> du document pour les rendre disponibles */

  var circles = document.querySelectorAll('.net-area svg circle');
  /* Sélectionne tous les éléments <circle> du SVG de l'illustration réseau */

  /* Tableau des animations à appliquer, avec durée, timing et délai de démarrage */
  var anims = [
    'floatA 3s ease-in-out infinite',        /* Nœud 1 : 3 secondes, sans délai */
    'floatB 3.7s ease-in-out infinite .4s',  /* Nœud 2 : 3.7 secondes, démarre après 0.4s */
    'floatC 2.8s ease-in-out infinite .8s'   /* Nœud 3 : 2.8 secondes, démarre après 0.8s */
  ];

  var targets = [];
  /* Tableau qui contiendra uniquement les cercles "solides" (les nœuds principaux) */

  /* Parcourt tous les cercles du SVG pour identifier les nœuds principaux */
  circles.forEach(function (c) {
    var fill = c.getAttribute('fill');
    /* Récupère la couleur de remplissage du cercle */

    /* On anime seulement les cercles pleins (blanc, bleu, vert)
       et pas les cercles de halo qui ont des couleurs rgba() */
    if (fill === '#ffffff' || fill === '#6ea8fe' || fill === '#22c55e') {
      targets.push(c);
      /* Ajoute ce cercle à la liste des cibles à animer */
    }
  });

  /* Applique une animation différente à chacun des trois nœuds principaux */
  targets.forEach(function (c, i) {
    if (anims[i]) c.style.animation = anims[i];
    /* Applique l'animation correspondante (par index) si elle existe dans le tableau */
  });

});
/* Fin du DOMContentLoaded */
