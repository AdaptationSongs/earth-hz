from dash import dcc, html


def hour_list(minutes_after):
    return [{'label': '{n}:{m:02d}'.format(n=n, m=minutes_after), 'value': n} for n in range(0, 24)]


layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.H2('Visualize Machine Learning Results'),
    html.Div([
        'Label: ',
        html.Div([
            dcc.Dropdown(id='label-dropdown'),
        ], style={'width':'100%'}),
    ], style={'display': 'flex', 'margin-bottom': '0.5em'}),
    html.Div([
        'Probability range: ',
        dcc.Input(id='min-prob', type="number", min=0.0, max=1.0, value=0.99, debounce=True, className='form-control'),
        ' to ',
        dcc.Input(id='max-prob', type="number", min=0.0, max=1.0, value=1.0, debounce=True, className='form-control'),
    ], style={'display': 'flex', 'margin-bottom': '0.5em'}),
    html.Div([
        'Time range: ',
        html.Div([
            dcc.Dropdown(id='start-hour', options=hour_list(0), value=0, clearable=False),
        ], style={'width':'100%'}),
        ' to ',
        html.Div([
            dcc.Dropdown(id='end-hour', options=hour_list(59), value=23, clearable=False),
        ], style={'width':'100%'}),
    ], style={'display': 'flex', 'margin-bottom': '0.5em'}),
    html.Div([
        'Model: ',
        html.Div([
            dcc.Dropdown(id='model-dropdown'),
        ], style={'width':'100%'}),
        html.Div([
            dcc.Dropdown(id='iteration-dropdown'),
        ], style={'width':'100%'}),
    ], style={'display': 'flex', 'margin-bottom': '0.5em'}),
    dcc.Graph(id='daily-graph'),
    html.Div([
        dcc.Link(id='verify-link', href='#', children='', target='_blank')
    ]),
    dcc.Graph(id='hourly-graph'),
    dcc.Graph(id='file-graph'),
    dcc.Graph(id='hourly-file-graph'),
])
