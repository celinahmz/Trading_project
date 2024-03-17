import json
import os
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
import psycopg2

# Informations de connexion à la base de données Alwaysdata
with open(os.path.expandvars("config/bd_config.json")) as json_file:
    conn_params = json.load(json_file)

# Initialiser la variable conn en dehors du bloc try
conn = None

try:
    # Connexion à la base de données Alwaysdata
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True

    # Exécuter ici vos opérations sur la base de données...
    # Par exemple, créer une table

    # Exemple : Créer la table "data_cac40" avec quelques colonnes
    create_table_query = '''
        CREATE TABLE IF NOT EXISTS test_trading (
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

    # Maintenant, vous pouvez ajouter les données à cette table en utilisant SQLAlchemy

    # Créer une connexion à la base de données avec SQLAlchemy
    engine = create_engine(
        f'postgresql+psycopg2://{conn_params["user"]}:{conn_params["password"]}@{conn_params["host"]}:{conn_params["port"]}/{conn_params["database"]}')

    # Nom de la table dans la base de données
    nom_table = 'data_trading'

    # Charger le fichier Excel avec les noms et symboles du CAC 40
    company_referal_path = 'data/input/liste_cac40.xlsx'
    cac40_data = pd.read_excel(company_referal_path)

    # Créer un DataFrame pour stocker les données historiques
    historical_data = pd.DataFrame(columns=['Date et Heure', 'Open', 'High', 'Low', 'Close', 'Volume', 'Name'])

    # Définir la période de 2 an

    end_date = pd.to_datetime('today')
    start_date = end_date - pd.DateOffset(days=730) + pd.DateOffset(hours=9)

    # Boucle pour récupérer les données pour chaque symbole
    for index, row in cac40_data.iterrows():
        symbol = row['Symbol']
        name = row['Name']
        try:
            # Télécharger les données historiques avec un intervalle d'une heure
            data = yf.download(symbol, start=start_date, end=end_date, interval='1h')

            # Filtrer les données pour ne conserver que celles de 9h à 19h
            data = data.between_time('09:00', '17:00')

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

    try:
        # Ajouter les données dans la table PostgreSQL
        historical_data.to_sql(nom_table, con=engine, index=False, if_exists='replace')

        print(f"Données ajoutées avec succès à la table '{nom_table}' dans la base de données.")

    except Exception as e:
        print(f"Erreur lors de l'insertion des données historiques : {e}")

    finally:
        # Fermer la connexion dans tous les cas
        engine.dispose()

except psycopg2.Error as e:
    print("Erreur lors de la connexion à la base de données ou de la création de la table :")
    print(e)

finally:
    # Fermer la connexion dans tous les cas
    if conn is not None:
        conn.close()

excel_output_path = 'historical_data_cac40.xlsx'
historical_data.to_excel(excel_output_path, index=False)
print(f"Données historiques sauvegardées avec succès dans '{excel_output_path}'.")
