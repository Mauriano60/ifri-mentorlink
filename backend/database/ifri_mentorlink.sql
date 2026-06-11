CREATE DATABASE IF NOT EXISTS ifri_mentorlink CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ifri_mentorlink;

DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS participants_conversation;
DROP TABLE IF EXISTS conversations;
DROP TABLE IF EXISTS competences_utilisateur;
DROP TABLE IF EXISTS difficultes_utilisateur;
DROP TABLE IF EXISTS correspondances;
DROP TABLE IF EXISTS offre_mentorat;
DROP TABLE IF EXISTS demande_mentorat;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS disponibilites;
DROP TABLE IF EXISTS parametres;
DROP TABLE IF EXISTS utilisateurs;
DROP TABLE IF EXISTS filieres_etudes;
DROP TABLE IF EXISTS niveaux_etudes;
DROP TABLE IF EXISTS matieres;

CREATE TABLE matieres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE filieres_etudes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE niveaux_etudes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    telephone VARCHAR(20) UNIQUE NOT NULL,
    mot_de_passe VARCHAR(255) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    biographie TEXT,
    email_verifie TINYINT(1) DEFAULT 0,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    est_actif TINYINT(1) DEFAULT 1,
    id_filiere INT NOT NULL,
    id_niveau INT NOT NULL,
    --  Champs pour la récupération de mot de passe oublié
    -- reset_token : token généré et envoyé par email à l'utilisateur 
    -- reset_expire : date/heure d'expiration du token
    reset_token VARCHAR(255) DEFAULT NULL,
    reset_expire DATETIME DEFAULT NULL,
    FOREIGN KEY (id_filiere) REFERENCES filieres_etudes(id) ON DELETE CASCADE,
    FOREIGN KEY (id_niveau) REFERENCES niveaux_etudes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE parametres (
    id_parametres INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL UNIQUE,
    visibilite_profil VARCHAR(20) DEFAULT 'public',
    email_notification TINYINT(1) DEFAULT 1,
    push_notification TINYINT(1) DEFAULT 1,
    new_match_alerts TINYINT(1) DEFAULT 1,
    weekly_summary TINYINT(1) DEFAULT 1,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE competences_utilisateur (
    utilisateur_id INT NOT NULL,
    matiere_id INT NOT NULL,
    PRIMARY KEY(utilisateur_id, matiere_id),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (matiere_id) REFERENCES matieres(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE difficultes_utilisateur (
    utilisateur_id INT NOT NULL,
    matiere_id INT NOT NULL,
    PRIMARY KEY(utilisateur_id, matiere_id),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (matiere_id) REFERENCES matieres(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE disponibilites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    jour_semaine VARCHAR(20) NOT NULL,
    heure_debut TIME NOT NULL,
    heure_fin TIME NOT NULL,
    CHECK (heure_debut < heure_fin),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE offre_mentorat (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    matiere_id INT NOT NULL,
    format VARCHAR(20) NOT NULL,
    description TEXT,
    statut_offre TINYINT(1) DEFAULT 1,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (format IN ('en_ligne', 'presentiel', 'les_deux')),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (matiere_id) REFERENCES matieres(id)
) ENGINE=InnoDB;

CREATE TABLE demande_mentorat (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    matiere_id INT NOT NULL,
    format VARCHAR(20) NOT NULL,
    description TEXT,
    statut_demande TINYINT(1) DEFAULT 1,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (format IN ('en_ligne', 'presentiel', 'les_deux')),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (matiere_id) REFERENCES matieres(id)
) ENGINE=InnoDB;

CREATE TABLE correspondances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mentor_id INT NOT NULL,
    mentee_id INT NOT NULL,
    score_compatibilite DECIMAL(5,2) NOT NULL,
    statut_correspondance INT DEFAULT 0,
    initiateur_id INT NULL,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mentor_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (mentee_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (initiateur_id) REFERENCES utilisateurs(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE participants_conversation (
    conversation_id INT NOT NULL,
    utilisateur_id INT NOT NULL,
    PRIMARY KEY (conversation_id, utilisateur_id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    expediteur_id INT NOT NULL,
    contenu TEXT NOT NULL,
    envoye_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (expediteur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    correspondance_id INT NULL,
    message TEXT NOT NULL,
    type_notification VARCHAR(50) DEFAULT 'info',
    est_lu TINYINT(1) DEFAULT 0,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB;



-- INDEXATION DES TABLES POUR OPTIMISER LES REQUÊTES
CREATE INDEX idx_utilisateurs_actif ON utilisateurs(est_actif);
CREATE INDEX idx_offre_utilisateur_statut ON offre_mentorat(utilisateur_id, statut_offre, matiere_id);
CREATE INDEX idx_demande_utilisateur_statut ON demande_mentorat(utilisateur_id, statut_demande, matiere_id);
CREATE INDEX idx_correspondances_membres_statut ON correspondances(mentor_id, mentee_id, statut_correspondance);
CREATE INDEX idx_correspondances_initiateur ON correspondances(initiateur_id);
CREATE INDEX idx_notifications_utilisateur_lu ON notifications(utilisateur_id, est_lu);



INSERT INTO matieres (nom) VALUES
('Logique, arithmétique et applications'),
('Algèbre linéaire et applications'),
('Analyse et applications'),
('Probabilité et statistique'),
('Architecture et topologie des réseaux informatiques'),
('Système d exploitation et outils de base en informatique'),
('Base de la programmation'),
('Déontologie et droit liés aux TIC'),
('Techniques d expression écrite et orale'),
('Programmation Python'),
('Base de données relationnelles'),
('Technologies web et infographie'),
('Mathématiques appliquées'),
('Projet intégrateur'),
('Administration des réseaux sous Windows/Linux'),
('Convergence et calcul différentiel'),
('Anglais technique'),
('Structures algébriques et leurs applications en informatique'),
('Approche orientée objet'),
('Structures de données et applications avec C/Python'),
('Administration systèmes et réseaux'),
('Sécurité des systèmes informatiques'),
('Management de la sécurité du système d information'),
('Sécurité des réseaux'),
('Maintenance des appareils électroniques'),
('Politique de sécurité des systèmes d information'),
('Commutation et routage'),
('Audit, normes de sécurité et gestion des risques et incidents'),
('Sécurisation des réseaux sans fil'),
('Cryptographie et applications'),
('Gestion des projets'),
('Communication managériale'),
('Anglais pour la communication scientifique'),
('Programmation avancée en Java'),
('Programmation graphique en Qt/C++'),
('Aspects avancés des technologies web'),
('Bases du génie logiciel'),
('Programmation avancée en Python et R'),
('Structure de données avancées'),
('Aspects avancés des bases de données'),
('Système d information décisionnelle'),
('Ingénierie logicielle et les PGI/ERP'),
('Cycle de vie d un logiciel et assurance qualité');


INSERT INTO filieres_etudes (nom) VALUES
('Génie Logiciel'), ('Sécurité Informatique'), ('Intelligence Artificielle'), ('Internet et Multimédia'), ('Systèmes embarqués et Internet des Objets');

INSERT INTO niveaux_etudes (nom) VALUES
('Licence 1'), ('Licence 2'), ('Licence 3');

INSERT INTO utilisateurs (email, telephone, mot_de_passe, prenom, nom, id_filiere, id_niveau, biographie, email_verifie, est_actif)
VALUES
('mentor@ifri.test', '97000001', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi.', 'Aminata', 'Mensah', 1, 3, 'Je peux aider en web, bases de donnees et methodologie de projet.', 1, 1),
('mentee@ifri.test', '97000002', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi.', 'Koffi', 'Dossou', 2, 1, 'Je cherche un accompagnement regulier pour progresser en programmation.', 1, 1);

INSERT INTO competences_utilisateur (utilisateur_id, matiere_id) VALUES 
(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11),(1,12),(1,13),(1,14),(1,15),(1,16),(1,17),(1,18),(1,19),(1,20),(1,21),(1,22),(1,23),(1,24),(1,25),(1,26),(1,27),(1,28),(1,29),(1,30),(1,31),(1,32),(1,33),(1,34),(1,35),(1,36),(1,37),(1,38),(1,39),(1,40),(1,41),(1,42),(1,43);

INSERT INTO difficultes_utilisateur (utilisateur_id, matiere_id) VALUES 
(2,1),(2,2),(2,3),(2,4),(2,5),(2,6),(2,7),(2,8),(2,9),(2,10),(2,11),(2,12),(2,13),(2,14),(2,15),(2,16),(2,17),(2,18),(2,19),(2,20),(2,21),(2,22),(2,23),(2,24),(2,25),(2,26),(2,27),(2,28),(2,29),(2,30),(2,31),(2,32),(2,33),(2,34),(2,35),(2,36),(2,37),(2,38),(2,39),(2,40),(2,41),(2,42),(2,43);

INSERT INTO disponibilites (utilisateur_id, jour_semaine, heure_debut, heure_fin)
VALUES (1, 'Samedi', '09:00:00', '12:00:00'), (2, 'Samedi', '10:00:00', '13:00:00');

INSERT INTO offre_mentorat (utilisateur_id, matiere_id, format, description)
VALUES
(1, 3, 'les_deux', 'Sessions pratiques pour comprendre HTML, CSS, PHP et les bases MVC.');
INSERT INTO demande_mentorat (utilisateur_id, matiere_id, format, description)
VALUES
(2, 2, 'en_ligne', 'Besoin d aide pour SQL, jointures et conception de schema.');
INSERT INTO correspondances (mentor_id, mentee_id, score_compatibilite) VALUES (1, 2, 85.00);
INSERT INTO conversations () VALUES ();
INSERT INTO participants_conversation (conversation_id, utilisateur_id) VALUES (1, 1), (1, 2);
INSERT INTO messages (conversation_id, expediteur_id, contenu) VALUES (1, 1, 'Bonjour Koffi, ravi de te rencontrer! Je suis Aminata, ton mentor pour la programmation web. N hesite pas a me poser toutes tes questions.'), (1, 2, 'Bonjour Aminata, merci de m accompagner! J ai deja quelques questions sur les bases de donnees, notamment les jointures. Pourrais tu m expliquer comment elles fonctionnent?');
INSERT INTO notifications (utilisateur_id, message) VALUES 
(1, 'Bienvenue sur IFRI MentorLink !'), 
(2, 'Bienvenue sur IFRI MentorLink !');
INSERT INTO parametres (utilisateur_id, visibilite_profil, email_notification, push_notification, new_match_alerts, weekly_summary) VALUES (1, 'public', 1, 1, 1, 1), (2, 'public', 1, 1, 1, 1);
