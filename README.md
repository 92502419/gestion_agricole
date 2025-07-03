MonPlanting - Journal Agricole
Description
MonPlanting est une application web développée avec Streamlit pour aider les agriculteurs à gérer leurs activités agricoles. Elle permet de suivre les parcelles, les activités, les rappels, et offre des analyses statistiques détaillées grâce à une interface utilisateur intuitive. L'application utilise une base de données SQLite pour stocker les données et intègre des visualisations interactives avec Plotly.
L'objectif principal est de fournir un outil simple mais puissant pour :

Gérer les parcelles agricoles (nom, surface, localisation, type de sol, etc.).
Enregistrer les activités agricoles (semis, plantation, arrosage, etc.) avec des détails comme la date, le coût, et les conditions météorologiques.
Programmer des rappels pour les tâches à venir.
Visualiser les données sous forme de graphiques et de calendriers pour une meilleure prise de décision.


Fonctionnalités principales

Gestion des utilisateurs :

Inscription et connexion sécurisées avec hachage des mots de passe (SHA-256).
Authentification basée sur un nom d'utilisateur et un mot de passe.


Gestion des parcelles :

Création, visualisation et gestion des parcelles agricoles.
Enregistrement des détails comme la surface, la localisation, le type de sol et une description.


Suivi des activités :

Enregistrement des activités agricoles (ex. : semis, fertilisation, récolte) avec des informations détaillées (type de culture, quantité, coût, météo, etc.).
Filtrage des activités par type, culture ou période.
Visualisation des activités sous forme de graphiques (diagrammes à barres, courbes, etc.).


Gestion des rappels :

Planification de rappels pour les tâches agricoles avec des alertes urgentes pour les échéances proches ou dépassées.
Possibilité de marquer les rappels comme terminés.


Calendrier agricole :

Vue mensuelle des activités et rappels avec un affichage clair des tâches par jour.
Filtrage par mois et année.


Analyses et statistiques :

Visualisations des données agricoles (répartition des activités, coûts, activités par parcelle, etc.).
Graphiques interactifs (diagrammes en secteurs, courbes temporelles, cartes thermiques).
Métriques clés comme le coût total, le coût moyen, et le type d'activité le plus fréquent.


Interface utilisateur :

Interface moderne avec des styles CSS personnalisés pour une expérience utilisateur fluide.
Navigation intuitive via une barre latérale.
Affichage responsive avec des onglets, des formulaires et des cartes métriques.




Prérequis
Pour exécuter l'application, les dépendances suivantes doivent être installées :

Python (>= 3.8)
Bibliothèques Python :
streamlit : Framework pour l'interface web.
sqlite3 : Gestion de la base de données.
pandas : Manipulation des données.
plotly : Visualisations graphiques interactives.
hashlib : Hachage des mots de passe.
datetime : Gestion des dates.



Vous pouvez installer les dépendances avec la commande suivante :
pip install streamlit pandas plotly


Installation

Cloner le projet :
git clone <URL_DU_DÉPÔT>
cd monplanting


Installer les dépendances :
pip install -r requirements.txt


Créer un fichier requirements.txt (si non fourni) :
streamlit
pandas
plotly


Lancer l'application :
streamlit run app.py


Accéder à l'application via le navigateur à l'adresse : http://localhost:8501.



Structure du projet
monplanting/
│
├── app.py                  # Script principal de l'application
├── monplanting.db          # Base de données SQLite (créée automatiquement)
├── README.md               # Documentation du projet
└── requirements.txt        # Liste des dépendances

Détails du fichier app.py

Configuration de la page : Utilisation de st.set_page_config pour définir le titre, l'icône et la disposition.
Styles CSS personnalisés : Définition des styles pour les en-têtes, cartes métriques, boutons, etc.
Classe DatabaseManager : Gestion de la base de données SQLite avec des méthodes pour :
Créer et initialiser les tables (users, parcelles, activities, reminders).
Gérer les utilisateurs (inscription, authentification).
Gérer les parcelles, activités et rappels (ajout, récupération, mise à jour).


Classe MonPlantingApp : Logique principale de l'application avec des méthodes pour :
Page de connexion/inscription.
Tableau de bord avec métriques et graphiques.
Gestion des parcelles, activités, rappels, calendrier et analyses.


Exécution : Point d'entrée avec app.run().

Structure de la base de données
La base de données SQLite (monplanting.db) contient les tables suivantes :

users :

id : Identifiant unique.
username : Nom d'utilisateur (unique).
email : Adresse email (unique).
password_hash : Mot de passe haché.
created_at : Date de création.


parcelles :

id : Identifiant unique.
user_id : Référence à l'utilisateur.
name : Nom de la parcelle.
surface : Surface en hectares.
location : Localisation.
soil_type : Type de sol.
description : Description.
created_at : Date de création.


activities :

id : Identifiant unique.
parcelle_id : Référence à la parcelle.
activity_type : Type d'activité (ex. : semis, récolte).
date : Date de l'activité.
crop_type : Type de culture.
variety : Variété.
quantity : Quantité.
unit : Unité de mesure.
notes : Notes supplémentaires.
cost : Coût de l'activité.
weather_conditions : Conditions météorologiques.
created_at : Date de création.


reminders :

id : Identifiant unique.
parcelle_id : Référence à la parcelle.
activity_type : Type d'activité.
reminder_date : Date du rappel.
title : Titre du rappel.
description : Description.
is_completed : Statut (terminé ou non).
created_at : Date de création.




Utilisation

Connexion/Inscription :

Accédez à la page d'accueil pour vous connecter ou créer un compte.
Fournissez un nom d'utilisateur, un email et un mot de passe pour l'inscription.
Connectez-vous avec vos identifiants.


Tableau de bord :

Consultez les métriques clés (nombre de parcelles, surface totale, activités récentes, rappels en attente).
Visualisez les graphiques de répartition des activités et l'évolution temporelle.


Gestion des parcelles :

Ajoutez une nouvelle parcelle avec ses détails.
Consultez la liste des parcelles et leurs informations.


Gestion des activités :

Sélectionnez une parcelle et ajoutez des activités (ex. : semis, arrosage).
Filtrez les activités par type, culture ou période.
Visualisez les graphiques d'analyse (coûts, évolution temporelle).


Gestion des rappels :

Programmez des rappels pour les tâches à venir.
Consultez les rappels en attente et marquez-les comme terminés.


Calendrier :

Affichez les activités et rappels pour un mois donné.
Visualisez les tâches par jour avec des détails.


Analyses :

Consultez les métriques détaillées (total des activités, coûts, etc.).
Explorez les graphiques interactifs (diagrammes en secteurs, courbes, cartes thermiques).


Limitations

Base de données : SQLite est utilisé pour sa simplicité, mais peut ne pas convenir à une utilisation à grande échelle.
Sécurité : Le hachage SHA-256 est basique ; pour une application en production, envisagez un hachage plus sécurisé (ex. : bcrypt).
Déploiement : L'application est conçue pour une exécution locale avec Streamlit. Pour un déploiement en production, des ajustements (serveur, base de données, etc.) sont nécessaires.


Améliorations futures

Ajout de notifications par email ou SMS pour les rappels urgents.
Intégration de prévisions météorologiques via une API.
Exportation des données (PDF, CSV, etc.).
Support multilingue.
Gestion des cultures avec des recommandations basées sur le type de sol et le climat.


Licence
Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

Contact
Pour toute question ou suggestion, contactez l'équipe de développement sur :

Email : [2419richardo@gmail.com]
