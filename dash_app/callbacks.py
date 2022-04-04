from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from sqlalchemy import func, extract, desc
from app import db
from app.models import Label, MLModel, ModelIteration, ModelLabel, StatusEnum
from dash_app.util import get_q


def register_callbacks(dashapp):


    @dashapp.callback(Output('start-hour', 'value'), [Input('start-hour', 'value')], [State('end-hour', 'value')])
    def validate_start_hour(start, end):
        if start > end:
           new_start = end
           return new_start
        else:
           raise PreventUpdate


    @dashapp.callback(Output('end-hour', 'value'), [Input('end-hour', 'value')], [State('start-hour', 'value')])
    def validate_end_hour(end, start):
        if end < start:
           new_end = start
           return new_end
        else:
           raise PreventUpdate


    @dashapp.callback(Output('model-dropdown', 'options'), [Input('url', 'search')])
    def update_model_options(query):
        try:
            project_id = get_q(query, 'project')
            with dashapp.server.app_context():
                results = db.session.query(MLModel.id, MLModel.name, func.max(ModelIteration.updated).label('latest')).join(MLModel).filter(MLModel.project_id == project_id).group_by(MLModel.id).order_by(desc('latest')).all()
            options = [{'label': r.name, 'value': r.id} for r in results]
        except:
             options = []
        return options


    @dashapp.callback(Output('model-dropdown', 'value'), [Input('model-dropdown', 'options')])
    def update_model_default(options):
        return options[0]['value']


    @dashapp.callback(Output('iteration-dropdown', 'options'), [Input('model-dropdown', 'value')])
    def update_iteration_options(selected_model_id):
        try:
            results = ModelIteration.query.filter(ModelIteration.model_id == selected_model_id).filter(ModelIteration.status == StatusEnum.finished).order_by(ModelIteration.updated.desc()).all()
            options = [{'label': r.updated, 'value': r.id} for r in results]
        except:
             options = []
        return options


    @dashapp.callback(Output('iteration-dropdown', 'value'), [Input('iteration-dropdown', 'options')])
    def update_iteration_default(options):
        return options[0]['value']


    @dashapp.callback(Output('label-dropdown', 'options'), [Input('iteration-dropdown', 'value')])
    def update_label_options(selected_iteration_id):
        try:
            results = ModelLabel.query.filter(ModelLabel.iteration_id == selected_iteration_id, ModelLabel.combine_with_id == None).join(Label, ModelLabel.label_id == Label.id).order_by(Label.name).all()
            options = [{'label': str(r.label), 'value': r.label_id} for r in results]
        except:
             options = []
        return options
