// ════════════════════════════════
// ANIMATION COMPTEURS (section stats foncée)
// ════════════════════════════════

// Sélectionne tous les éléments avec la classe .big-stat-number
const counters = document.querySelectorAll('.big-stat-number');

// Durée totale de l'animation en millisecondes
const duration = 2000;

// Fonction qui anime un seul compteur de 0 jusqu'à data-target
function animateCounter(el) {

  // Lit la valeur cible depuis l'attribut HTML data-target
  const target = parseInt(el.getAttribute('data-target'));

  // Calcule combien ajouter à chaque frame pour atteindre la cible en 2s à 60fps
  const increment = target / ((duration / 1000) * 60);

  // Valeur courante du compteur, commence à 0
  let current = 0;

  // Lance une boucle qui tourne 60 fois par seconde
  const timer = setInterval(() => {

    current += increment; // Incrémente la valeur courante

    if (current >= target) {
      // Quand on atteint ou dépasse la cible
      el.textContent = target; // Affiche exactement la valeur cible
      clearInterval(timer);    // Arrête la boucle
    } else {
      // Sinon affiche la valeur arrondie à l'entier inférieur
      el.textContent = Math.floor(current);
    }

  }, 1000 / 60); // Intervalle = 16.67ms ≈ 60fps
}


// ════════════════════════════════
// INTERSECTION OBSERVER
// Déclenche l'animation quand la
// section devient visible à l'écran
// ════════════════════════════════

// Crée un observateur de visibilité
const observer = new IntersectionObserver((entries) => {

  entries.forEach(entry => {

    if (entry.isIntersecting) {
      // L'élément est visible dans le viewport

      animateCounter(entry.target); // Lance l'animation
      observer.unobserve(entry.target); // Ne rejoue qu'une seule fois
    }
  });

}, {
  threshold: 0.3 // Se déclenche quand 30% de l'élément est visible
});

// Attache l'observateur à chaque compteur
counters.forEach(counter => observer.observe(counter));


// ════════════════════════════════
// NAVBAR : OMBRE AU SCROLL
// Ajoute une ombre sous la navbar
// quand l'utilisateur fait défiler
// ════════════════════════════════

// Récupère la navbar par son id
const navbar = document.getElementById('mainNav');

// Écoute l'événement scroll sur toute la fenêtre
window.addEventListener('scroll', () => {

  if (window.scrollY > 10) {
    // Si scrollé de plus de 10px
    navbar.style.boxShadow = '0 2px 16px rgba(0,0,0,0.08)';
    // Applique une ombre légère sous la navbar
  } else {
    // Retour en haut de page : retire l'ombre
    navbar.style.boxShadow = 'none';
  }

});
