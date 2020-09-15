import dash_core_components as dcc
import dash_html_components as html


layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.H2('Visualize Machine Learning Results'),
    html.Div([
        'Label: ',
        dcc.Dropdown(id='label-dropdown', style={'width': '50%'}),
    ], style={'display': 'flex', 'line-height': '2em', 'margin-bottom': '0.5em'}),
    html.Div([
        'Probability range: ', 
        dcc.Input(id='min-prob', type="number", min=0.0, max=1.0, value=0.99, debounce=True, style={'verticalAlign': 'middle'}),
        ' to ',
        dcc.Input(id='max-prob', type="number", min=0.0, max=1.0, value=1.0, debounce=True, style={'verticalAlign': 'middle'}),
    ], style={'display': 'flex', 'line-height': '2em', 'margin-bottom': '0.5em'}),
    html.Div([
        'Model: ',
        dcc.Dropdown(id='model-dropdown', style={'width': '100%'}),
        dcc.Dropdown(id='iteration-dropdown', style={'width': '100%'}),
    ], style={'display': 'flex', 'width': '50%', 'line-height': '2em', 'margin-bottom': '0.5em'}),
    dcc.Graph(id='daily-graph'),
    dcc.Graph(id='hourly-graph')
], style={'width': '500'})
