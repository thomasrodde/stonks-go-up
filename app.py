# Import current yahoo finance API, data manipulation, dash modules

import yfinance as yf
from datetime import date
from dateutil.relativedelta import relativedelta
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Output, Input
import requests

# Current reported fields: price history, recent price comparisons

external_stylesheets = [
    {
        'href': 'https://fonts.googleapis.com/css2?'
        'family=Lato:wght@400;700&display=swap',
        'rel': 'stylesheet',
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = 'Stock Advisor'

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children='🤑', className='header-emoji'),
                html.H1(
                    children='Stock Advisor', className='header-title'
                ),
                html.P(
                    children='Track the trended prices of stocks '
                    'and assess sell/buy activities.',
                    className='header-description',
                ),
            ],
            className='header',
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children='Company Search', className='menu-title'),
                        dcc.Input(id='company-name', value='Alphabet Inc', type='search')
                        ]
                        ),
                html.Div(
                    children=[
                        html.Div(children='Symbol Search', className='menu-title'),
                        dcc.Input(id='company-symbol', value='GOOGL', type='search')
                        ]
                        ),
                html.Div(
                    children=[
                        html.Div(
                            children='Date Range',
                            className='menu-title'
                            ),
                        dcc.DatePickerRange(
                            id='date-range',
                            min_date_allowed='1900-01-01',
                            max_date_allowed=date.today(),
                            start_date=date.today() - relativedelta(days = 365),
                            end_date=date.today()
                        )])
            ],
            className='menu',
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                    dcc.Loading(
                        id='loading-1',
                        type='default',
                        children=[
                        html.Div(children=[
                            html.Div(children=[
                                html.Div(children='Name:',
                                 className='menu-title',
                                  style={'display': 'inline-block', 'padding': '5px'}),
                                html.Div(id = 'company_name', style={'display': 'inline-block'})]),
                            html.Div(children=[
                                html.Div(children='Symbol: ',
                                 className='menu-title',
                                  style={'display': 'inline-block', 'padding': '5px'}),
                                html.Div(id = 'company_symbol', style={'display': 'inline-block'})])],
                            className='subtitle'),
                        html.Div(children=[
                            dcc.Graph(id='trended-chart',config={'displayModeBar': False})],
                            className='card'),
                        html.Div(children=[
                            dcc.Graph(id='compared-chart', config={'displayModeBar': False})],
                            className='card'),
                        ],
                        )
                    ],
                    )
                ],
                className='wrapper'
                )
        ]
        )

# To process filters and user input, we'll callback to the Yahoo API data source.
# The trend and price comparison charts should update simultaneously.
@app.callback(
    [
        Output('trended-chart', 'figure'),
        Output('compared-chart', 'figure'),
        Output('company_symbol', 'children'),
        Output('company_name', 'children')
     ],
    [
        Input('company-symbol', 'value'),
        Input('company-name', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
    ],
)
def update_charts(symbol, name, start_date, end_date):
    
    # Trended prices are updated when the user selects a symbol and start/end dates
    # Declaring the API call as an initial variable avoids making excessive calls and slowing down chart loading
    
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    stripped_name = name \
    .replace('.', '') \
	.replace(',', '') \
	.replace(' Inc', '') \
	.replace(' ', '') \
	.replace(' inc', '') \
	.replace("'", '') \
	.lower()
    
    api_key='SI7YWG525NBBUL1O'

    if input_id == 'company-symbol':
    	company_name =  yf.Ticker(symbol).info['shortName']
    	company_symbol = symbol
    	stock_ticker = yf.Ticker(symbol)
    elif stripped_name == 'google':
    	company_name =  yf.Ticker('GOOG').info['shortName']
    	company_symbol = 'GOOG'
    	stock_ticker = yf.Ticker('GOOG')
    else:
    	r = requests.get('https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={}&apikey={}'.format(stripped_name, api_key)).json()['bestMatches']
    	sym_initial = pd.DataFrame(r)
    	sym = sym_initial[~sym_initial['1. symbol'].str.contains('.', regex=False)]
    	company_symbol = list(sym['1. symbol'])[0]
    	company_name = list(sym['2. name'])[0]
    	stock_ticker = yf.Ticker(company_symbol)

    # We build the dataframe using the ticker symbol

    trended_prices = pd.DataFrame(
        stock_ticker
        .history(start = start_date, end=(pd.to_datetime(end_date) + relativedelta(days=1)))['Close']
        ).rename(columns = {'Close': company_symbol}).reset_index()
    trended_chart_figure = {
        'data': [
            {
                'x': trended_prices['Date'],
                'y': trended_prices[company_symbol],
                'type': 'lines',
                'hovertemplate': '$%{y:.2f}<extra></extra>',
            },
        ],
        'layout': {
            'title': {
                'text': 'Trended Stock Price',
                'x': 0.05,
                'xanchor': 'left',
            },
            'xaxis': {'fixedrange': True},
            'yaxis': {'tickprefix': '$', 'fixedrange': True},
            'colorway': ['#17B897'],
        },
    }
    # Compared prices are updated when the user selects a symbol or company
    compared_prices = pd.DataFrame({
        'ticker': [company_symbol],
    	'Two Hundred Day Average': [stock_ticker.info['twoHundredDayAverage']],
    	'Fifty Day Average': [stock_ticker.info['fiftyDayAverage']],
    	'Previous Close': [stock_ticker.info['previousClose']]}) \
        .melt(id_vars=['ticker'], 
               var_name=['Type'],
               value_name='Value')
    x=compared_prices['Type']
    y=compared_prices['Value']
    z=compared_prices['ticker']

    compared_chart_figure = go.Figure(
        data=[go.Bar(
        x=x,
        y=y,
        text=y,
        customdata=z, 
        textposition='outside',
        marker=dict(color='LightSeaGreen'),
        hovertemplate='<br>'
        .join(['Ticker: %{customdata}<extra></extra>',
               'Type: %{x}',
               'Value: %{y}'
              ]),
        texttemplate='%{y}'
        )])
    # We have to make some layout tweaks to match the trended chart's styling
    compared_chart_figure.update_yaxes(# Prices are in dollars
        tickprefix='$', showgrid=True
        )
    compared_chart_figure.update_layout(title = 'Interday Price Comparisons',
                  yaxis_title=None,
                  xaxis_title=None,
                  barmode='group',
                  template='plotly_white',)
    return trended_chart_figure, compared_chart_figure, company_symbol, company_name


if __name__ == '__main__':
    app.run_server(debug=True)



