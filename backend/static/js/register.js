document.addEventListener('DOMContentLoaded', function () {

  var step1 = document.getElementById('step1');
  var step2 = document.getElementById('step2');
  var btnSuivant = document.getElementById('btnSuivant');
  var btnRetour = document.getElementById('btnRetour');
  var btnInscrire = document.getElementById('btnInscrire');
  var registerForm = document.getElementById('registerForm');
  var currentStep = document.getElementById('currentStep');

  var nom = document.getElementById('nom');
  var prenom = document.getElementById('prenom');
  var email = document.getElementById('email');
  var telephone = document.getElementById('telephone');
  var motdepasse = document.getElementById('motdepasse');
  var confirmer = document.getElementById('confirmer');

  var filiere = document.getElementById('filiere');
  var niveau = document.getElementById('niveau');

  var fieldsStep1 = [nom, prenom, email, telephone, motdepasse, confirmer];

  fieldsStep1.forEach(function (champ) {
    if (champ) {
      champ.addEventListener('input', function () {
        champ.classList.remove('is-invalid');
      });
    }
  });

  if (currentStep && currentStep.value === '2') {
    step1.style.display = 'none';
    step2.style.display = 'block';
    document.getElementById('stepCircle1').classList.remove('active');
    document.getElementById('stepCircle1').classList.add('completed');
    document.getElementById('stepCircle1').innerHTML = '<i class="bi bi-check-lg"></i>';
    document.getElementById('stepLabel1').classList.remove('fw-bold');
    document.getElementById('stepLabel1').classList.add('text-muted');
    document.getElementById('stepCircle2').classList.add('active');
    document.getElementById('stepLabel2').classList.remove('text-muted');
    document.getElementById('stepLabel2').classList.add('fw-bold');
    document.getElementById('stepLine1').classList.add('step-line-done');
  }

  function validerEtape1() {
    fieldsStep1.forEach(function (champ) {
      if (champ) champ.classList.remove('is-invalid', 'is-valid');
    });
    var ok = true;
    if (nom.value.trim() === '') { nom.classList.add('is-invalid'); ok = false; }
    if (prenom.value.trim() === '') { prenom.classList.add('is-invalid'); ok = false; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) { email.classList.add('is-invalid'); ok = false; }
    if (telephone.value.trim() === '') { telephone.classList.add('is-invalid'); ok = false; }
    if (motdepasse.value.length < 8) { motdepasse.classList.add('is-invalid'); ok = false; }
    if (confirmer.value !== motdepasse.value || confirmer.value === '') { confirmer.classList.add('is-invalid'); ok = false; }
    return ok;
  }

  if (btnSuivant) {
    btnSuivant.addEventListener('click', function () {
      if (validerEtape1()) {
        if (currentStep) currentStep.value = '2';
        step1.style.display = 'none';
        step2.style.display = 'block';

        document.getElementById('stepCircle1').classList.remove('active');
        document.getElementById('stepCircle1').classList.add('completed');
        document.getElementById('stepCircle1').innerHTML = '<i class="bi bi-check-lg"></i>';
        document.getElementById('stepLabel1').classList.remove('fw-bold');
        document.getElementById('stepLabel1').classList.add('text-muted');

        document.getElementById('stepCircle2').classList.add('active');
        document.getElementById('stepLabel2').classList.remove('text-muted');
        document.getElementById('stepLabel2').classList.add('fw-bold');

        document.getElementById('stepLine1').classList.add('step-line-done');
      }
    });
  }

  if (btnRetour) {
    btnRetour.addEventListener('click', function () {
      if (currentStep) currentStep.value = '1';
      step2.style.display = 'none';
      step1.style.display = 'block';

      document.getElementById('stepCircle1').classList.add('active');
      document.getElementById('stepCircle1').classList.remove('completed');
      document.getElementById('stepCircle1').innerHTML = '1';
      document.getElementById('stepLabel1').classList.add('fw-bold');
      document.getElementById('stepLabel1').classList.remove('text-muted');

      document.getElementById('stepCircle2').classList.remove('active');
      document.getElementById('stepLabel2').classList.remove('fw-bold');
      document.getElementById('stepLabel2').classList.add('text-muted');

      document.getElementById('stepLine1').classList.remove('step-line-done');
    });
  }

  if (filiere) {
    filiere.addEventListener('change', function () {
      filiere.classList.remove('is-invalid');
    });
  }

  if (niveau) {
    niveau.addEventListener('change', function () {
      niveau.classList.remove('is-invalid');
    });
  }

  var competencesListe = document.getElementById('competences');
  var lacunesListe = document.getElementById('lacunes');

  function desactiverItemsCommuns() {
    var compIds = [];
    competencesListe.querySelectorAll('li.selected').forEach(function (li) {
      compIds.push(li.dataset.valeur);
    });

    lacunesListe.querySelectorAll('li').forEach(function (li) {
      if (compIds.indexOf(li.dataset.valeur) !== -1) {
        li.classList.remove('selected');
        li.classList.add('disabled-item');
      } else {
        li.classList.remove('disabled-item');
      }
    });

    var lacIds = [];
    lacunesListe.querySelectorAll('li.selected').forEach(function (li) {
      lacIds.push(li.dataset.valeur);
    });

    competencesListe.querySelectorAll('li').forEach(function (li) {
      if (lacIds.indexOf(li.dataset.valeur) !== -1) {
        li.classList.remove('selected');
        li.classList.add('disabled-item');
      } else {
        li.classList.remove('disabled-item');
      }
    });
  }

  function initBulletList(listeId) {
    var liste = document.getElementById(listeId);
    if (!liste) return;
    var items = liste.querySelectorAll('li');
    items.forEach(function (item) {
      item.addEventListener('click', function () {
        if (item.classList.contains('disabled-item')) return;

        var estSelection = item.classList.contains('selected');
        var maxAtteint = liste.querySelectorAll('li.selected').length >= 4;

        if (!estSelection && maxAtteint) {
          afficherErreur(listeId, 'Maximum 4 sélections autorisées.');
          return;
        }

        item.classList.toggle('selected');
        retirerErreur(listeId);
        desactiverItemsCommuns();
      });
    });
  }

  initBulletList('competences');
  initBulletList('lacunes');

  function syncHiddenInputs() {
    var anciens = document.querySelectorAll('.bullet-hidden');
    anciens.forEach(function (e) { e.remove(); });

    document.querySelectorAll('.bullet-list').forEach(function (liste) {
      var name = liste.id === 'competences' ? 'competences' : 'lacunes';
      liste.querySelectorAll('li.selected').forEach(function (item) {
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = item.dataset.valeur;
        input.className = 'bullet-hidden';
        registerForm.appendChild(input);
      });
    });
  }

  function afficherErreur(listeId, message) {
    var existant = document.getElementById('erreur-' + listeId);
    if (existant) return;
    var err = document.createElement('p');
    err.id = 'erreur-' + listeId;
    err.className = 'text-danger small mt-1';
    err.textContent = message;
    document.getElementById(listeId).insertAdjacentElement('afterend', err);
  }

  function retirerErreur(listeId) {
    var e = document.getElementById('erreur-' + listeId);
    if (e) e.remove();
  }

  function validerEtape2() {
    filiere.classList.remove('is-invalid', 'is-valid');
    niveau.classList.remove('is-invalid', 'is-valid');
    retirerErreur('competences');
    retirerErreur('lacunes');

    var ok = true;
    if (!filiere.value) { filiere.classList.add('is-invalid'); ok = false; }
    if (!niveau.value) { niveau.classList.add('is-invalid'); ok = false; }

    var nbComp = competencesListe.querySelectorAll('li.selected').length;
    var nbLac = lacunesListe.querySelectorAll('li.selected').length;

    if (nbComp === 0) { afficherErreur('competences', 'Veuillez sélectionner au moins une compétence.'); ok = false; }
    if (nbComp > 4) { afficherErreur('competences', 'Maximum 4 compétences autorisées.'); ok = false; }
    if (nbLac === 0) { afficherErreur('lacunes', 'Veuillez sélectionner au moins une lacune.'); ok = false; }
    if (nbLac > 4) { afficherErreur('lacunes', 'Maximum 4 lacunes autorisées.'); ok = false; }

    return ok;
  }

  if (btnInscrire) {
    btnInscrire.addEventListener('click', function () {
      if (validerEtape2()) {
        syncHiddenInputs();
        registerForm.submit();
      }
    });
  }

  document.querySelectorAll('.toggle-password').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var target = document.getElementById(this.dataset.target);
      if (!target) return;
      var icon = this.querySelector('i');
      if (target.type === 'password') {
        target.type = 'text';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
      } else {
        target.type = 'password';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
      }
    });
  });

});
