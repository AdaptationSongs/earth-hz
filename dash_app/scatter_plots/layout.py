from dash import dcc, html
import dash_bootstrap_components as dbc
from dash_app.layout import prediction_filters


layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.Breadcrumb(id='breadcrumbs'),
    dbc.Container([
        html.H2('Scatter Plots'),
        prediction_filters,
        dcc.Graph(id='daily-graph'),
        dcc.Graph(id='hourly-graph'),
        dcc.Graph(id='file-graph'),
        dcc.Graph(id='hourly-file-graph'),
    ], fluid=True),
    dbc.Offcanvas([
        dcc.Link('Verify results for selected day / time at this location', id='verify-link', href='#', target='_blank'),
    ], id='more-info', placement='bottom', scrollable=True, backdrop=False, is_open=False),

])
