# trading_project

# Configuration et Exécution

## Prérequis
- Python et librairies importées dans le code 
utiliser la commande : **pip install -r requirement.txt**
pour installer les librairies nécessaire a l'execution des scripts.
- PostgreSQL : Nous utilisons pgAdmin4 pour l'administration et le requêtage de la base de données (optional).

## Configuration
1. Clonez le projet depuis GitHub :

    ```bash
    git clone https://github.com/celinahmz/trading_project.git
    cd trading_IntelliTrade_prj
    ```

2. Placez les fichiers sources dans le répertoire spécifié.



## Exécution
1. Lancez le terminal a partir du fichier :
Sur la ligne de commande, sur le dossier du projet, tapez :
    python real_time extraction.py (Pour le scrapping en temps réel)
    python history_extract.py (Pour l'extraction des données historique)
    python finacial_prediction.py (Pour les algorithme de prédiction)

    ```
Ou a partir de votre IDE de prédilection.

2. Si vous lancez le script financial_prediction accédez à l'interface Web du script à l'adresse [http://127.0.0.1:8050/](http://127.0.0.1:8050/).


# Schéma de la Base de données



                                        +------------------------+
                                        | data_trading           |
                                        |------------------------|
                                        | Name                   |
                                        | Open                   |
                                        | Close                  |
                                        | Volume                 |
                                        | date_et_heure          |
                                        +------------------------+



# Alimentation de la base de données

Afin de passer les données d'une tâche à une autre, nous avons utilisé des fichiers de sauvegarde temporaires. . Pour l'insertion, nous avons crée une connexion avec une base de données SQL, puis à partir des DataFrames de données nous avons effectuée les insertions au sein de la table.

Pour plus d'informations, consultez les sections spécifiques du code et les commentaires correspondants.


# Envoi de mail 

Une fonction d'envoi de messages à partie la boîte mail "rpa.trading.symphonie@gmail.com" a été mise en place pour recevoir les notifications a la cloture du marché. Des blocs try-except ont été ajoutés, ainsi que des retours BOOLEAN dans toutes les tâches afin de vérifier la réussite de leur exécution. Ces vérifications se font à l'aide d'opérateurs "AND" car (True and True and...True = True). Il suffit qu'un seul élément soit False pour déclencher l'envoi d'un mail d'erreur.

le fichier de configuration est dans : [lien vers le fichier de configuration de mail](/config/mail_config.json)
le contenu du mail de l'insertion est de ce format :

INFO : Valeurs des actions du CAC40 du 08/03/2024 Groupe 02

Bonjour,

        Le marché EuroNextParis vient de cloturé.

        Veuillez trouver ci-joint le fichier contenant les données des entreprises du CAC40 pour le 08/03/2024.

        Cordialement,


        Trading-Bot

        IntelliTrade

---

*Ce projet a été réalisé par Dhia Eddin FILLALI, Célina HAMZAOUI, Sarah ASSAM, Sedik BENMESSAOUD.*
*Sup de Vinci 2024.*
