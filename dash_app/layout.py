from dash import dcc, html
import dash_bootstrap_components as dbc


def hour_list(minutes_after):
    return [{'label': '{h}:{m:02d}'.format(h=hour, m=minutes_after), 'value': hour} for hour in range(0, 24)]


prediction_filters = html.Div([
    dbc.Row([
        dbc.Label('Label:', html_for='label-dropdown', width='auto'),
        dbc.Col([
            dcc.Dropdown(id='label-dropdown'),
        ]),
    ]),
     dbc.Row([
        dbc.Label('Probability range:', html_for='min-prob', width='auto'),
        dbc.Col([
            dbc.Input(id='min-prob', type="number", min=0.0, max=1.0, value=0.99, debounce=True),
        ]),
        dbc.Label('to', html_for='max-prob', width='auto'),
        dbc.Col([
            dbc.Input(id='max-prob', type="number", min=0.0, max=1.0, value=1.0, debounce=True),
        ]),
    ]),
    dbc.Row([
        dbc.Label('Time range:', html_for='start-hour', width='auto'),
        dbc.Col([
            dcc.Dropdown(id='start-hour', options=hour_list(0), value=0, clearable=False),
        ]),
        dbc.Label('to', html_for='end-hour', width='auto'),
        dbc.Col([
            dcc.Dropdown(id='end-hour', options=hour_list(59), value=23, clearable=False),
         ]),
    ]),
    dbc.Row([
        dbc.Label('Model:', html_for='model-dropdown', width='auto'),
        dbc.Col([
            dcc.Dropdown(id='model-dropdown'),
        ]),
        dbc.Col([
            dcc.Dropdown(id='iteration-dropdown'),
        ]),
    ]),
])
