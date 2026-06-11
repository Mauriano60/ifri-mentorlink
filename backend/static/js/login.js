/* =========================================================
   IFRI_MentorLink — login.js
   Gestion des interactions de la page de connexion
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

  var emailInput = document.getElementById('email');
  var pwInput = document.getElementById('password');
  var loginForm = document.getElementById('loginForm');
  var errEmail = document.getElementById('err-email');
  var errPw = document.getElementById('err-pw');

  if (emailInput) {
    emailInput.addEventListener('input', function () {
      emailInput.classList.remove('error');
      errEmail.textContent = '';
    });
  }

  if (pwInput) {
    pwInput.addEventListener('input', function () {
      pwInput.classList.remove('error');
      errPw.textContent = '';
    });
  }

  if (loginForm) {
    loginForm.addEventListener('submit', function (e) {
      var email = emailInput ? emailInput.value.trim() : '';
      var password = pwInput ? pwInput.value.trim() : '';
      var ok = true;

      emailInput.classList.remove('error');
      pwInput.classList.remove('error');
      errEmail.textContent = '';
      errPw.textContent = '';

      if (!email) {
        emailInput.classList.add('error');
        errEmail.textContent = 'Veuillez saisir votre email ou téléphone.';
        ok = false;
      }

      if (!password) {
        pwInput.classList.add('error');
        errPw.textContent = 'Veuillez saisir votre mot de passe.';
        ok = false;
      }

      if (!ok) {
        e.preventDefault();
      }
    });
  }

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
