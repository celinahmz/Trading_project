import json
import os
import dash
from dash import dcc, html, Input, Output
import dash.exceptions
import yfinance as yf
from prophet import Prophet
import pandas as pd
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.arima.model import ARIMA
import numpy as np
from sqlalchemy import create_engine
from googlesearch import search
import requests
from transformers import BertTokenizer, BertForSequenceClassification

# Create the Dash application
app = dash.Dash(__name__)

# Informations de connexion à la base de données Alwaysdata
with open(os.path.expandvars("config/bd_config.json")) as json_file:
    conn_params = json.load(json_file)

engine = create_engine(
    f'postgresql+psycopg2://{conn_params["user"]}:{conn_params["password"]}@{conn_params["host"]}:{conn_params["port"]}/{conn_params["database"]}')
query = "SELECT * from data_trading;"
df = pd.read_sql(query, engine)
companies = df['Name'].unique()


# Function to get Google search results
def get_google_search_results(query, num_results=5):
    results = list(search(query, num_results=num_results))
    return results


# Function to analyze sentiment of financial news
def analyze_sentiment(text):
    tokenizer = BertTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
    model = BertForSequenceClassification.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")

    # Use the model to predict sentiment
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model(**inputs)
    logits = outputs.logits
    sentiment_scores = logits.softmax(dim=1).tolist()[0]

    return sentiment_scores


# Function to get financial news
def get_financial_news(api_key, query):
    base_url = 'https://newsapi.org/v2/everything'
    params = {
        'q': query,
        'apiKey': api_key
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        articles = data['articles']
        return articles
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []


# Define the layout
app.layout = html.Div([
    dcc.Dropdown(
        id='symbol-input',
        options=[{'label': company, 'value': company} for company in companies],
        value=None,
        placeholder="Select a company for models"
    ),
    dcc.Graph(id='graph-1'),
    dcc.Dropdown(
        id='dropdown-1',
        options=[
            {'label': 'Prophet', 'value': 'prophet'},
            {'label': 'All', 'value': 'All'},
            {'label': 'Linear Regression', 'value': 'sklearn'},
            {'label': 'ARIMA', 'value': 'arima'}
        ],
        value='All',
        clearable=False
    ),
    html.Div([
        html.Button('Chercher les concurrents', id='google-search-button', n_clicks=0),
        html.Button('Analyser les news financières', id='sentiment-analysis-button', n_clicks=0),
        html.Div(id='google-search-results'),
        html.Div(id='sentiment-analysis-results')
    ])
])


# Callback to display the prediction of the selected model
@app.callback(
    Output('graph-1', 'figure'),
    [Input('dropdown-1', 'value'),
     Input('symbol-input', 'value')]
)
def update_figure(model_name, symbol):
    if not symbol:
        raise dash.exceptions.PreventUpdate

    start_date = '2022-04-01'
    end_date = pd.to_datetime('today')
    query = "SELECT * from data_trading;"
    df = pd.read_sql(query, engine)

    prices = df.loc[df['Name'] == symbol]
    df = prices.reset_index()
    df = df.rename(columns={'Date et Heure': 'ds', 'Close': 'y'})

    model_prophet = Prophet()
    train_data = df[df['ds'] <= '2024-01-01']
    model_prophet.fit(train_data)

    future_prophet = model_prophet.make_future_dataframe(periods=365)
    forecast_prophet = model_prophet.predict(future_prophet)
    ci_prophet = forecast_prophet[['ds', 'yhat_lower', 'yhat_upper']]

    X_train = np.arange(len(df)).reshape(-1, 1)
    y_train = df['y']
    y_train.interpolate(inplace=True)

    model_sklearn = LinearRegression()
    model_sklearn.fit(X_train, y_train)

    order = (5, 1, 2)
    model_arima = ARIMA(df['y'], order=order)
    results_arima = model_arima.fit()
    y_pred_arima = results_arima.predict(start=len(df), end=len(df) + 700, typ='levels')

    X_future = np.arange(len(df), len(df) + 180).reshape(-1, 1)
    y_pred_sklearn = model_sklearn.predict(X_future)

    if model_name == 'All':
        return {
            'data': [
                {'x': df['ds'], 'y': df['y'], 'name': 'Actual Data'},
                {'x': forecast_prophet['ds'], 'y': forecast_prophet['yhat'], 'name': 'Prophet'},
                {'x': ci_prophet['ds'], 'y': ci_prophet['yhat_upper'], 'name': 'Prophet Upper',
                 'line': {'dash': 'dash'}},
                {'x': ci_prophet['ds'], 'y': ci_prophet['yhat_lower'], 'name': 'Prophet Lower',
                 'line': {'dash': 'dash'}},
                {'x': pd.date_range(start='2024-01-01', end='2024-06-01', freq='D'), 'y': y_pred_sklearn,
                 'name': 'Linear Regression'},
                {'x': pd.date_range(start='2024-01-01', end='2024-06-01', freq='D'), 'y': y_pred_arima, 'name': 'ARIMA'}
            ],
            'layout': {'xaxis': {'title': 'Date'}, 'yaxis': {'title': 'Adjusted Value'},
                       'legend': {'orientation': 'horizontal'}}
        }
    elif model_name == 'sklearn':
        return {
            'data': [
                {'x': df['ds'], 'y': df['y'], 'name': 'Actual Data'},
                {'x': pd.date_range(start='2024-01-01', end='2024-06-01', freq='D'), 'y': y_pred_sklearn,
                 'name': 'Linear Regression'}
            ],
            'layout': {'xaxis': {'title': 'Date'}, 'yaxis': {'title': 'Adjusted Value'},
                       'legend': {'orientation': 'horizontal'}}
        }
    elif model_name == 'prophet':
        return {
            'data': [
                {'x': df['ds'], 'y': df['y'], 'name': 'Actual Data'},
                {'x': forecast_prophet['ds'], 'y': forecast_prophet['yhat'], 'name': 'Prophet'},
                {'x': ci_prophet['ds'], 'y': ci_prophet['yhat_upper'], 'name': 'Prophet Upper',
                 'line': {'dash': 'dash'}},
                {'x': ci_prophet['ds'], 'y': ci_prophet['yhat_lower'], 'name': 'Prophet Lower',
                 'line': {'dash': 'dash'}}
            ],
            'layout': {'xaxis': {'title': 'Date'}, 'yaxis': {'title': 'Adjusted Value'},
                       'legend': {'orientation': 'horizontal'}}
        }
    elif model_name == 'arima':
        return {
            'data': [
                {'x': df['ds'], 'y': df['y'], 'name': 'Actual Data'},
                {'x': pd.date_range(start='2024-01-01', end='2024-06-01', freq='D'), 'y': y_pred_arima, 'name': 'ARIMA'}
            ],
            'layout': {'xaxis': {'title': 'Date'}, 'yaxis': {'title': 'Adjusted Value'},
                       'legend': {'orientation': 'horizontal'}}
        }
    else:
        raise ValueError(f"Invalid model name: {model_name}")


# Callback to display Google search results
@app.callback(
    Output('google-search-results', 'children'),
    [Input('google-search-button', 'n_clicks')],
    [dash.dependencies.State('symbol-input', 'value')]
)
def google_search(n_clicks, selected_company):
    if n_clicks > 0 and selected_company:
        query = "Conncurrent de " + selected_company
        google_results = get_google_search_results(query)
        result_text = f"**Résultat de recherche :'{selected_company}':**<br><br>"
        for result in google_results:
            result_text += f" - <div style='font-weight: bold;'>{result}</div><br>"
        return dcc.Markdown(result_text, dangerously_allow_html=True)
    else:
        return ''


# Callback to analyze sentiment of financial news
@app.callback(
    Output('sentiment-analysis-results', 'children'),
    [Input('sentiment-analysis-button', 'n_clicks')],
    [dash.dependencies.State('symbol-input', 'value')]
)
def sentiment_analysis_v1(n_clicks, selected_company, api_key='c40a2774baaa4761b2093bb360c23a1b'):
    """Analyzes sentiment of financial news for the given company.

    Args:
        n_clicks: Number of clicks (potentially used for triggering analysis).
        selected_company: Name of the company to analyze.
        api_key: API key for accessing financial news data (placeholder).

    Returns:
        A string containing the formatted sentiment analysis results,
        or an error message if analysis fails.
    """

    if n_clicks > 0 and selected_company:
        try:
            articles = get_financial_news("c40a2774baaa4761b2093bb360c23a1b", selected_company)

            if not articles:
                result_text = "<li>Pas de d'autualités financières à analyser  </li>"
            else:
                result_text = f"**Analyses des News  for '{selected_company}':**<br><br>"
                result_text += "<ul>"  # Start of bulleted list

                for article in articles:
                    article_summary = article['content']
                    title = article['title']

                    if selected_company.lower() in str(title).lower():
                        result_text += f"<li><div style='font-weight: bold;'>{title}</div></li>"

                        # Sentiment analysis with BERT model (implementation not provided)
                        sentiment_scores = analyze_sentiment(article_summary)  # Replace with actual implementation
                        sentiment_label, best_sentiment_score, confidence_score = process_sentiment_scores(
                            sentiment_scores)  # Refactored for clarity

                        result_text += f"<div>Sentiment : {sentiment_label}</div>"
                        result_text += f"<div>Score correspondant : {best_sentiment_score}</div>"
                        result_text += f"<div>Certitude du Sentiment : {confidence_score}</div><br>"

                        result_text += f"</ul>"  # End of bulleted list

                return dcc.Markdown(result_text, dangerously_allow_html=True)
        except ConnectionError as e:
            return f"Error connecting to financial news service: {e}"
        except ValueError as e:
            return f"Invalid data received from financial news service: {e}"
        except Exception as e:
            return f"Error analyzing sentiment: {e}"
    else:
        return ''


def process_sentiment_scores(sentiment_scores):
    """Processes sentiment scores and returns labels for clarity.

    Args:
      sentiment_scores: A list of sentiment scores (implementation not provided).

    Returns:
      A tuple containing the sentiment label (e.g., "Positive"),
      the best sentiment score, and the sentiment certainty score.
    """

    max_sentiment_score_index = sentiment_scores.index(max(sentiment_scores))
    sentiment_label = ['Trés Negative', 'Negative', 'Neutre', 'Positive', 'Trés Positive'][max_sentiment_score_index]
    best_sentiment_score = sentiment_scores[max_sentiment_score_index]
    second_best_score = sorted(sentiment_scores, reverse=True)[1]
    confidence_score = best_sentiment_score - second_best_score

    return sentiment_label, best_sentiment_score, confidence_score


# Run the Dash application
if __name__ == '__main__':
    app.run_server(debug=True)