import yfinance as yf
import pandas as pd
import datetime
from pytz import timezone  # Importer la classe timezone de la bibliothèque pytz

# Charger le fichier Excel avec les noms et symboles du CAC 40
company_referal_path = 'liste_cac40.xlsx'
cac40_data = pd.read_excel(company_referal_path)

# Créer un DataFrame pour stocker les données historiques
historical_data = pd.DataFrame(columns=['Date et Heure', 'Open', 'High', 'Low', 'Close', 'Volume', 'Name'])

# Définir la période d'un an
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=365)

# Boucle pour récupérer les données pour chaque symbole
for index, row in cac40_data.iterrows():
    symbol = row['Symbol']
    name = row['Name']
    try:
        # Télécharger les données historiques avec un intervalle d'une heure
        data = yf.download(symbol, start=start_date, end=end_date, interval='1h')

        # Filtrer les données pour ne conserver que celles de 9h à 17h35
        data = data.between_time('09:00', '18:00')

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
historical_data = historical_data[['Name', 'Open', 'High', 'Low', 'Close', 'Volume','Date et Heure' ]]

# Enregistrer les données dans un fichier Excel avec la colonne "Date et Heure"
historical_data.to_excel('historique_cac40.xlsx', index=False)