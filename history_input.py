import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
import psycopg2

# Informations de connexion à la base de données Alwaysdata
conn_params = {
    'database': 'projetbourse_trading',
    'user': 'projetbourse_',
    'password': 'SSDC2024',
    'host': 'postgresql-projetbourse.alwaysdata.net',
    'port': '5432'
}

# Initialiser la variable conn en dehors du bloc try
conn = None

# Initialiser le DataFrame global
historical_data = pd.DataFrame(columns=['Date et Heure', 'Open', 'High', 'Low', 'Close', 'Volume', 'Name'])

# Créer une connexion à la base de données avec SQLAlchemy
engine = create_engine(f'postgresql+psycopg2://{conn_params["user"]}:{conn_params["password"]}@{conn_params["host"]}:{conn_params["port"]}/{conn_params["database"]}')

# Nom de la table dans la base de données
nom_table = 'data'

# Début du script interactif
while True:
    print("\nOptions disponibles:")
    print("0. Exécuter toutes les étapes (0)")
    print("1. Récuperer les données historiques (1)")
    print("2. Créer un fichier Excel avec les données historiques (2)")
    print("3. Se connecter à la base de données (3)")
    print("4. Créer la table dans la base de données (4)")
    print("5. Alimenter la table avec les données historiques (5)")
    print("6. Changer la période d'historique (6)")
    print("7. Quitter le script (7)")

    choix = input("Choisissez une option (0,1,2,3,4,5,6,7): ")

    if choix == '0':
        try:
            
            # Récupérer les données historiques
            company_referal_path = 'liste_cac40.xlsx'
            cac40_data = pd.read_excel(company_referal_path)
            historical_data = pd.DataFrame(columns=['Date et Heure', 'Open', 'High', 'Low', 'Close', 'Volume', 'Name'])
            end_date = pd.to_datetime('today')
            start_date = end_date - pd.DateOffset(days=365) + pd.DateOffset(hours=9)
            for index, row in cac40_data.iterrows():
                symbol = row['Symbol']
                name = row['Name']
                try:
                    data = yf.download(symbol, start=start_date, end=end_date, interval='1h')
                    data = data.between_time('09:00', '19:00')
                    data['Name'] = name
                    historical_data = pd.concat([historical_data, data], ignore_index=False)
                except Exception as e:
                    print(f"Erreur lors du téléchargement des données pour {symbol}: {e}")

            historical_data.index = pd.to_datetime(historical_data.index)
            historical_data['Date et Heure'] = historical_data.index.strftime('%Y-%m-%d %H:%M:%S')
            historical_data = historical_data[['Name', 'Open', 'High', 'Low', 'Close', 'Volume', 'Date et Heure']]

            print("Données historiques récupérées avec succès.")

            # Créer un fichier Excel avec les données historiques
            excel_output_path = 'historical_data_cac40.xlsx'
            historical_data.to_excel(excel_output_path, index=False)
            print(f"Données historiques sauvegardées avec succès dans '{excel_output_path}'.")

            # Se connecter à la base de données
            conn = psycopg2.connect(**conn_params)
            conn.autocommit = True
            print("Connexion à la base de données établie avec succès.")

            # Créer la table dans la base de données
            create_table_query = '''
                CREATE TABLE IF NOT EXISTS data (
                    Name VARCHAR(255),
                    Open FLOAT,
                    High FLOAT,
                    Low FLOAT,
                    Close FLOAT,
                    Volume FLOAT,
                    Date_et_Heure TIMESTAMP
                );
            '''
            with conn.cursor() as cursor:
                cursor.execute(create_table_query)
                print("La table 'data' a été créée avec succès.")


            # Alimenter la table avec les données historiques
            historical_data.to_sql(nom_table, con=engine, index=False, if_exists='replace')
            print(f"Données ajoutées avec succès à la table '{nom_table}' dans la base de données.")

        except psycopg2.Error as e:
            print("Erreur lors de l'exécution des étapes :")
            print(e)

        finally:
            # Fermer la connexion dans tous les cas
            if conn is not None:
                conn.close()

    elif choix == '1':
        try:
            # Connexion à la base de données Alwaysdata
            conn = psycopg2.connect(**conn_params)
            conn.autocommit = True

            # Charger le fichier Excel avec les noms et symboles du CAC 40
            company_referal_path = 'liste_cac40.xlsx'
            cac40_data = pd.read_excel(company_referal_path)

            # Réinitialiser le DataFrame global
            historical_data = pd.DataFrame(columns=['Date et Heure', 'Open', 'High', 'Low', 'Close', 'Volume', 'Name'])

            # Définir la période d'un an
            end_date = pd.to_datetime('today')
            start_date = end_date - pd.DateOffset(days=365) + pd.DateOffset(hours=9)

            # Boucle pour récupérer les données pour chaque symbole
            for index, row in cac40_data.iterrows():
                symbol = row['Symbol']
                name = row['Name']
                try:
                    # Télécharger les données historiques avec un intervalle d'une heure
                    data = yf.download(symbol, start=start_date, end=end_date, interval='1h')

                    # Filtrer les données pour ne conserver que celles de 9h à 19h
                    data = data.between_time('09:00', '19:00')

                    # Ajouter la colonne "Name" à toutes les lignes
                    data['Name'] = name

                    # Ajouter les données au DataFrame global
                    historical_data = pd.concat([historical_data, data], ignore_index=False)
                except Exception as e:
                    print(f"Erreur lors du téléchargement des données pour {symbol}: {e}")

            # Convertir l'index en DatetimeIndex et ajouter une colonne "Date et Heure" au format souhaité
            historical_data.index = pd.to_datetime(historical_data.index)
            historical_data['Date et Heure'] = historical_data.index.strftime('%Y-%m-%d %H:%M:%S')

            # Réorganiser les colonnes dans l'ordre souhaité
            historical_data = historical_data[['Name', 'Open', 'High', 'Low', 'Close', 'Volume', 'Date et Heure']]

            print("Données historiques récupérées avec succès.")

    
        except Exception as e:
            print(f"Erreur lors de la récupération et de l'enregistrement des données historiques : {e}")
        finally:
            # Fermer la connexion dans tous les cas
            if conn is not None:
                conn.close()

    elif choix == '2':
        # Créer un fichier Excel avec les données historiques
        excel_output_path = 'historical_data_cac40.xlsx'
        historical_data.to_excel(excel_output_path, index=False)
        print(f"Données historiques sauvegardées avec succès dans '{excel_output_path}'.")

    elif choix == '3':
        # Se connecter à la base de données
        try:
            conn = psycopg2.connect(**conn_params)
            conn.autocommit = True
            print("Connexion à la base de données établie avec succès.")
        except psycopg2.Error as e:
            print("Erreur lors de la connexion à la base de données :")
            print(e)

    elif choix == '4':
        # Créer la table dans la base de données
        if conn is not None:
            try:
                create_table_query = '''
                    CREATE TABLE IF NOT EXISTS data (
                        Name VARCHAR(255),
                        Open FLOAT,
                        High FLOAT,
                        Low FLOAT,
                        Close FLOAT,
                        Volume FLOAT,
                        Date_et_Heure TIMESTAMP
                    );
                '''
                with conn.cursor() as cursor:
                    cursor.execute(create_table_query)
                    print("La table 'data' a été créée avec succès.")
            except psycopg2.Error as e:
                print("Erreur lors de la création de la table :")
                print(e)
        else:
            print("Veuillez d'abord vous connecter à la base de données (option 'c').")

    elif choix == '5':
        # Alimenter la table avec les données historiques
        if conn is not None:
            try:
                historical_data.to_sql(nom_table, con=engine, index=False, if_exists='replace')
                print(f"Données ajoutées avec succès à la table '{nom_table}' dans la base de données.")
            except Exception as e:
                print(f"Erreur lors de l'insertion des données historiques : {e}")
        else:
            print("Veuillez d'abord vous connecter à la base de données (option 'c').")

    elif choix == '6':
        # Changer la période d'historique et l'intervalle
        cac40_data = pd.read_excel('liste_cac40.xlsx')
        nouvelle_periode = int(input("Entrez la nouvelle période en jours (par exemple, 365 pour un an) : "))
        nouvel_interval = input("Entrez le nouvel intervalle (par exemple, '1h' pour 1 heure) : ")

        try:
            # Calculer la nouvelle période
            end_date = pd.to_datetime('today')
            start_date = end_date - pd.DateOffset(days=nouvelle_periode) + pd.DateOffset(hours=9)

            # Réinitialiser le DataFrame global
            historical_data = pd.DataFrame(columns=['Date et Heure', 'Open', 'High', 'Low', 'Close', 'Volume', 'Name'])

            # Boucle pour récupérer les données pour chaque symbole
            for index, row in cac40_data.iterrows():
                symbol = row['Symbol']
                name = row['Name']
                try:
                    # Télécharger les données historiques avec le nouvel intervalle
                    data = yf.download(symbol, start=start_date, end=end_date, interval=nouvel_interval)

                    # Filtrer les données pour ne conserver que celles de 9h à 19h
                    data = data.between_time('09:00', '19:00')

                    # Ajouter la colonne "Name" à toutes les lignes
                    data['Name'] = name

                    # Ajouter les données au DataFrame global
                    historical_data = pd.concat([historical_data, data], ignore_index=False)
                except Exception as e:
                    print(f"Erreur lors du téléchargement des données pour {symbol}: {e}")

            # Mettre à jour la date
            # Convertir l'index en DatetimeIndex et ajouter une colonne "Date et Heure" au format souhaité
            historical_data.index = pd.to_datetime(historical_data.index)
            historical_data['Date et Heure'] = historical_data.index.strftime('%Y-%m-%d %H:%M:%S')

            # Réorganiser les colonnes dans l'ordre souhaité
            historical_data = historical_data[['Name', 'Open', 'High', 'Low', 'Close', 'Volume', 'Date et Heure']]
            print("Données historiques récupérées avec succès pour la nouvelle période et le nouvel intervalle.")

        except ValueError:
            print("Erreur : Veuillez entrer une valeur numérique pour la période.")
        except Exception as e:
            print(f"Erreur lors de la récupération et de l'enregistrement des données historiques : {e}")
        excel_output_path = 'historical_input.xlsx'
        historical_data.to_excel(excel_output_path, index=False)
        print(f"Données historiques sauvegardées avec succès dans '{excel_output_path}'.")

        # Afficher les données historiques

    elif choix == '7':
        # Quitter le script
        break

    else:
        print("Option invalide. Veuillez choisir une option valide.")