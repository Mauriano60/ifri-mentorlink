import re

def valider_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    return re.match(pattern, email) is not None

def valider_telephone(telephone):
    nettoye = telephone.replace(' ', '').replace('-', '').replace('.', '')
    if nettoye.startswith('+'):
        return nettoye.startswith('+229') and len(nettoye) >= 12 and nettoye[1:].isdigit()
    return nettoye.isdigit() and len(nettoye) >= 8

def valider_mot_de_passe(password):
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    if not any(c.isupper() for c in password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    if not any(c.isdigit() for c in password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    return True, None

def valider_inscription(form):
    erreurs = []

    if not form.get('prenom') or not form.get('nom'):
        erreurs.append("Prénom et nom obligatoires")

    if not valider_email(form.get('email', '')):
        erreurs.append("Email invalide")

    if not valider_telephone(form.get('telephone', '')):
        erreurs.append("Téléphone invalide")

    valide, msg = valider_mot_de_passe(form.get('password', ''))
    if not valide:
        erreurs.append(msg)

    if not form.get('id_filiere') or not form.get('id_niveau'):
        erreurs.append("Filière et niveau obligatoires")

    return erreurs

def valider_competences_et_lacunes(liste_competences, liste_lacunes):
    """
    Fonction de sécurité unifiée.
    Retourne (True, None) si tout est correct, ou (False, "Message d'erreur") en cas d'incohérence.
    """
    # 1. Limite stricte de 4 choix
    if len(liste_competences) > 4:
        return False, "Vous ne pouvez pas sélectionner plus de 4 compétences."
    if len(liste_lacunes) > 4:
        return False, "Vous ne pouvez pas sélectionner plus de 4 lacunes."
        
    # 2. Interdiction d'avoir une matière dans les deux listes
    set_competences = set(liste_competences)
    set_lacunes = set(liste_lacunes)
    
    if set_competences.intersection(set_lacunes):
        return False, "Une matière ne peut pas être simultanément une compétence et une lacune."
        
    return True, None