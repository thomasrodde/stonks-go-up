# Import current yahoo finance API, data manipulation, dash modules

import yfinance as yf
from datetime import date
from dateutil.relativedelta import relativedelta
import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import math
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Output, Input

trended_prices = pd.read_csv("trended_prices.csv")
compared_prices = pd.read_csv("compared_prices.csv")

labels = {0: 'GOOG'
, 1: 'NKE'
, 2: 'MSFT'
, 3: 'KO'
, 4: 'FB'
, 5: 'GME'
, 6: 'CRM'
, 7: 'DIS'
, 8: 'OTEX'
, 9: 'F'
, 10: 'SNAP'
, 11: 'MCD'
, 12: 'VTI'
, 13: 'AAPL'
, 14: 'NFLX'
, 15: 'TSLA'}

labels_list = list(labels.values())

ticker_tuples = ' '.join(labels_list)

tickers = yf.Tickers(ticker_tuples)

tickers_ls = list(tickers.tickers)

# Current reported fields: price history, recent price comparisons

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "Stonks Monitoring"

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children="🤑", className="header-emoji"),
                html.H1(
                    children="Stonks", className="header-title"
                ),
                html.P(
                    children="Track the trended prices of stocks "
                    "and assess sell/buy activities.",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Symbol", className="menu-title"),
                        dcc.Dropdown(
                            id="symbol-filter",
                            options=[
                                {"label": symbol, "value": symbol}
                                for symbol in np.sort(tickers_ls)
                            ],
                            value="GOOG",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Date Range",
                            className="menu-title"
                            ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed='2001-01-01',
                            max_date_allowed=date.today(),
                            start_date=date.today() - relativedelta(days = 365),
                            end_date=date.today(),
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="trended-chart", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="compared-chart", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)

# To process filters and user input, we'll callback to the Yahoo API data source.
# The trend and price comparison charts should update simultaneously.
@app.callback(
    [Output("trended-chart", "figure"), Output("compared-chart", "figure")],
    [
        Input("symbol-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(symbol, start_date, end_date):
    mask_trended = (
        (trended_prices.Date >= start_date)
        & (trended_prices.Date <= end_date)
    ) # the trended mask filters on date and symbol. 
    filtered_trended_prices = trended_prices.loc[mask_trended, ['Date', symbol]]
    trended_chart_figure = {
        "data": [
            {
                "x": filtered_trended_prices["Date"],
                "y": filtered_trended_prices[symbol],
                "type": "lines",
                "hovertemplate": "$%{y:.2f}<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Trended Price of the Stock",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True},
            "colorway": ["#17B897"],
        },
    }
    mask_compared = (
        (compared_prices.ticker == symbol)
    ) # the comparison mask filters on symbol only. 

    filtered_compared_chart = compared_prices.loc[mask_compared, :]

    x=filtered_compared_chart['Type']
    y=filtered_compared_chart['Value']
    z=filtered_compared_chart['ticker']

    compared_chart_figure = go.Figure(
        data=[go.Bar(
        x=x,
        y=y,
        text=y,
        customdata=z, 
        textposition='outside',
        marker=dict(color="LightSeaGreen"),
        hovertemplate="<br>"
        .join(["Ticker: %{customdata}<extra></extra>",
               "Type: %{x}",
               "Value: %{y}"
              ]),
        texttemplate='%{y}'
        )])
    
    compared_chart_figure.update_yaxes(# Prices are in dollars
        tickprefix="$", showgrid=True
        )
    compared_chart_figure.update_layout(title = 'Price Comparisons',
                  yaxis_title=None,
                  xaxis_title=None,
                  barmode='group',
                  template='plotly_white',)
    return trended_chart_figure, compared_chart_figure


if __name__ == "__main__":
    app.run_server(debug=True)



