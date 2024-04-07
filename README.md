# Consignes
Dans le cadre de la modernisation de son système d'information, la bibliothèque municipale vous demande de concevoir un système de gestion de son stock de livres. Afin de pouvoir gérer correctement cette bibliothèque, les utilisateurs du système doivent pouvoir :

- Ajouter, Modifier et Supprimer les auteurs
- Ajouter, Modifier et Supprimer les livres
- Gérer les emprunts de livres et le stock de livres



L’utilisation de l’application se fera via une API REST que vous implémenterez en suivant les best-practices.

Pour cet exercice aucune programmation HTML/CSS/JS n’est attendue, le système doit pouvoir se reposer entièrement sur les capacités de l’API pour administrer les différents composants de la bibliothèque.

En plus du code source Python 3, vous fournirez un dump de la base de données permettant de tester l’application, ainsi qu’un schéma UML au format png/jpeg justifiant l’implémentation de l'application proposée.

Bonus :
- Fournir un fichier docker-compose et ses fichiers dépendants avec votre code source permettant le test et le déploiement rapide de votre application et des différents composants.
- Endpoint de recherche d’un livre
- Gestion de l’authentification
- Schéma décrivant une possible solution de déploiement en production

# Installation and Deployment
### 1 - Clone this repository
### 2 - Install Docker
Get Docker here: https://docs.docker.com/get-docker/
_As of Docker 1.27.0, docker compose is intregrated in Docker._

_Please use `docker compose` which is the newest version and not `docker-compose`._
### 3 - cd into this folder
### 4 - Build the project
Run this command inside the project folder:
```bash
docker compose up -d --build
```
### 5 - Tests
To make sure everyting went well, you can run the tests inside the container:
```bash
docker compose exec fastapi-library-backend pytest . -vv
```

You should now have a working enviroment deployed with the FastAPI app and a working postgres database.

You can access the swagger UI on the following address: http://localhost:8000/docs#/

For a production deployment, some more configuration to the docker-compose.yml files will be necessary.

## Credentials
**Ideally, the env variables provided in the .env file would be stored in Gitlab Secrets or something similar.**

# Compte-rendu

## Choix techniques
Pour ce projet j'ai décidé de partir sur le framework FastAPI pour plusieurs raisons:
- Rapidité de développement

- Haute performance : FastAPI est construit sur Starlette et Pydantic, ce qui lui confère de très bonnes performances. Il prend en charge l'exécution asynchrone, ce qui permet de gérer efficacement de multiples requêtes en parallèle.

- Validation des données intégrée : FastAPI utilise Pydantic pour la validation des données, ce qui garantit que les données entrantes sont correctement vérifiées et typées avant d'être utilisées par l'application.

- Génération automatique de documentation : FastAPI génère automatiquement une documentation interactive Swagger UI et Redoc.

Pour la base de donnés j'ai décidé de partir sur PosgreSQL pour les raisons suivantes:
- Fiabilité et robustesse : PostgreSQL est réputé pour sa fiabilité, sa stabilité et sa robustesse. Il est largement utilisé dans les applications critiques où la disponibilité des données est cruciale.

- Prise en charge des transactions ACID : PostgreSQL prend en charge les transactions ACID (Atomicité, Cohérence, Isolation, Durabilité), ce qui garantit l'intégrité et la cohérence des données, même en cas de panne du système.

- Évolutivité : PostgreSQL est capable de gérer de grandes quantités de données et prend en charge la réplication, la partitionnement et d'autres fonctionnalités avancées pour assurer l'évolutivité de l'application.

Afin de ne pas écrire des modèles SQLAlchemy puis des schemas Pydantic, je suis parti sur la lib `SQLModel` qui à été écrite par le créateur de FastAPI et qui permet de déclarer les deux en même temps.

## Authentification

Afin de ne pas gérer les crédentials des utilisateurs moi-même, j'ai fait le choix d'utiliser le service d'authentification Auth0. Ce service propose également l'intégration du SSO ainsi que de la connexion avec des tiers comme Facebook, Google, Github, ...

J'ai créé sur Auth0 2 users, 1 admin et 1 member. Toutes les routes API sont protégées et accessibles uniquement par les **admins**. La seule exception étant la route `search_books(...)` qui est accessible par tous. Je pense que même des personnes n'étant pas membres peuvent être intéressé de savoir si le livre qu'ils veulent lire est disponible dans cette bibliothèque.

## Schema
![Database Schema](/images/db_schema_visual.png)

## Choix de conception de la base de données

Pour l'architecture de la base j'ai décidé de créer les tables suivantes. Je n'ai ajouté que les champs qui me sont venus à l'esprit mais des conditions professionnelles j'aurais passé un moment à mieux définir le périmètre et les valeurs nécessaires pour le client.

- **Members**: _Contient les membres qui se sont inscrits à la bibliothèque. On y trouve certaines informations comme le prénom, le nom de famille, l'id venant de auth0, la date d'expiration de la carte de bibliothèque,.._
- **Authors**: _Contient les auteurs créés. On y retrouve, le prénom, nom de famille, date de naissance, date de décès, ..._
- **AuthorBookLink**: _Table d'association afin d'établir un lien many-to-many entre Authors et Books. En effet, un livre peut avoir plusieurs auteurs et un auteur peut avoir écrit plusieurs livres._
- **Books**: _Contient les livres créés. On y retrouve, le titre du livre, sa date de parution, son ISBN, la langue, ..._
- **Copies**: _Contient les exemplaires créés. Par exemplaire j'entends, la version physique du livre. On pourra donc avoir 2 exemplaires du livre 'Twilight 1' par exemple. On y retrouve, le codebarre qui est souvent ajouté par les bibliothèques, si l'exemplaire est disponible ou non..._
- **Checkouts**: _Contient les emprunts créés. Lorsqu'un membre emprunte un livre, l'exemplaire passera en non-disponible et une nouvelle entrée dans la table sera ajoutée. On y retrouve la date d'emprunt, la date maximale de rendu autorisée et la date de retour._

## Prises de décision
- Un livre ne peut pas être créé sans auteurs.
- Un membre ne peut pas être supprimé s'il a déjà emprunté un livre, afin de conserver l'historique des emprunts.
- Un emprunt ne peut pas être supprimé tant que l'exemplaire n'a pas été restitué.

**Merci de ne pas vous attarder sur le contenu des données de test. Une partie à été générée de façon aléatoire et ne fait pas forcément sens.**

## Facteurs limitants et évolutivité
La principale limitation en termes d'évolutivité serait la table des emprunts, qui pourrait devenir très volumineuse avec le temps. Une stratégie d'archivage des emprunts anciens et une gestion efficace de la table permettraient de garantir la performance et l'évolutivité du système.
