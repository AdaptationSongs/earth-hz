from dash import dcc, html
import dash_bootstrap_components as dbc
from dash_app.layout import prediction_filters


layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.Container([
        dbc.Breadcrumb(id='breadcrumbs'),
        html.H2('Monthly Box Plots'),
        prediction_filters,
        dcc.Graph(id='monthly-grid'),
    ], fluid=True),
    dbc.Offcanvas([
        html.Ul([
            html.Li([
                dcc.Link('Verifiy predictions for month', id='month-link', href='#', target='_blank')
            ]),
            html.Li([
                dcc.Link(id='day-link', href='#', target='_blank')
            ], id='verify-day', hidden=True),
        ]),
    ], id='more-info', placement='bottom', scrollable=True, backdrop=False, is_open=False),
])
