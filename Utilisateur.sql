-- Création de la base de données
CREATE DATABASE IF NOT EXISTS UtilisateursDB;

-- Utiliser la base de données
USE UtilisateursDB;

-- Création de la table pour stocker les informations des utilisateurs
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom_utilisateur VARCHAR(50) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(255) NOT NULL
);

-- Création de la table des éléments (posts, commentaires, etc.) sur lesquels on peut interagir
CREATE TABLE IF NOT EXISTS elements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contenu TEXT NOT NULL,
    type_element ENUM('post', 'commentaire') NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création de la table de likes et dislikes
CREATE TABLE IF NOT EXISTS interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    element_id INT NOT NULL,
    type_interaction ENUM('LIKE', 'DISLIKE') NOT NULL,
    date_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_utilisateur FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    CONSTRAINT fk_element FOREIGN KEY (element_id) REFERENCES elements(id) ON DELETE CASCADE,
    CONSTRAINT unique_interaction UNIQUE (utilisateur_id, element_id, type_interaction)
);

-- Ajout de quelques indices pour améliorer les performances
CREATE INDEX idx_utilisateur_id ON interactions(utilisateur_id);
CREATE INDEX idx_element_id ON interactions(element_id);