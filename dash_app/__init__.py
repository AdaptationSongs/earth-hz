from flask.helpers import get_root_path
from flask_login import login_required
import dash
import dash_bootstrap_components as dbc


def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])


def register_dashapps(app):
    # Meta tags for viewport responsiveness
    meta_viewport = {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}
    stylesheets = [dbc.themes.BOOTSTRAP]

    from dash_app.scatter_plots.layout import layout as sp_layout
    from dash_app.scatter_plots.callbacks import register_callbacks as sp_register_callbacks
    scatter_plots = dash.Dash(__name__,
                         server=app,
                         url_base_pathname='/scatter_plots/',
                         assets_folder=get_root_path(__name__) + '/assets/',
                         meta_tags=[meta_viewport],
                         external_stylesheets=stylesheets
                   )
    with app.app_context():
        scatter_plots.title = 'Scatter plots'
        scatter_plots.layout = sp_layout
        sp_register_callbacks(scatter_plots)
    _protect_dashviews(scatter_plots)

    from dash_app.monthly_box_plots.layout import layout as mbp_layout
    from dash_app.monthly_box_plots.callbacks import register_callbacks as mbp_register_callbacks
    monthly_box_plots = dash.Dash(__name__,
                         server=app,
                         url_base_pathname='/monthly_box_plots/',
                         assets_folder=get_root_path(__name__) + '/assets/',
                         meta_tags=[meta_viewport],
                         external_stylesheets=stylesheets
                   )
    with app.app_context():
        monthly_box_plots.title = 'Monthly box plots'
        monthly_box_plots.layout = mbp_layout
        mbp_register_callbacks(monthly_box_plots)
    _protect_dashviews(monthly_box_plots)
