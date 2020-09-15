from datetime import datetime as dt
from urllib.parse import parse_qs
import pandas_datareader as pdr
from dash.dependencies import Input
from dash.dependencies import Output
import plotly_express as px
import pandas as pd
from sqlalchemy import func, extract, desc
from app import db
from app.models import ModelOutput, AudioFile, Equipment, MonitoringStation, Project, ProjectLabel, Label, MLModel, ModelIteration, ModelLabel


def register_callbacks(dashapp):


    @dashapp.callback(Output('model-dropdown', 'options'), [Input('url', 'search')])
    def update_model_options(query):
        try:
            query_dict = parse_qs(query[1:])
            project_id = query_dict['project'][0]
            with dashapp.server.app_context():
                results = db.session.query(MLModel.id, MLModel.name, func.max(ModelIteration.training_date).label('latest')).join(MLModel).filter(MLModel.project_id == project_id).group_by(MLModel.id).order_by(desc('latest')).all()
            options = [{'label': r.name, 'value': r.id} for r in results]
        except:
             options = []
        return options


    @dashapp.callback(Output('model-dropdown', 'value'), [Input('model-dropdown', 'options')])
    def update_model_options(options):
        return options[0]['value']


    @dashapp.callback(Output('iteration-dropdown', 'options'), [Input('model-dropdown', 'value')])
    def update_iteration_options(selected_model_id):
        try:
            results = ModelIteration.query.filter(ModelIteration.model_id == selected_model_id).order_by(ModelIteration.training_date.desc()).all() 
            options = [{'label': r.training_date, 'value': r.id} for r in results]
        except:
             options = []
        return options


    @dashapp.callback(Output('iteration-dropdown', 'value'), [Input('iteration-dropdown', 'options')])
    def update_iteration_options(options):
        return options[0]['value']


    @dashapp.callback(Output('label-dropdown', 'options'), [Input('iteration-dropdown', 'value')])
    def update_label_options(selected_iteration_id):
        try:
            results = ModelLabel.query.filter(ModelLabel.iteration_id == selected_iteration_id, ModelLabel.combine_with_id == None).join(Label, ModelLabel.label_id == Label.id).order_by(Label.name).all()
            options = [{'label': r.label.name, 'value': r.label_id} for r in results]
        except:
             options = []
        return options


    @dashapp.callback(Output('daily-graph', 'figure'), [Input('url', 'search'), Input('label-dropdown', 'value'), Input('min-prob', 'value'), Input('max-prob', 'value'), Input('iteration-dropdown', 'value')])
    def update_graph(query, selected_label_id, min_prob, max_prob, selected_iteration_id):
        try:
            query_dict = parse_qs(query[1:])
            project_id = query_dict['project'][0]
            with dashapp.server.app_context():
                per_file = db.session.query(ModelOutput.file_name, func.count(ModelOutput.id).label('count')).filter(ModelOutput.iteration_id == selected_iteration_id, ModelOutput.label_id == selected_label_id, ModelOutput.probability >= float(min_prob), ModelOutput.probability <= float(max_prob)).group_by(ModelOutput.file_name).subquery()
                per_day = db.session.query(MonitoringStation.name.label('station'), func.sum(per_file.columns.count).label('count'), func.date(AudioFile.timestamp).label('date')).join(AudioFile, per_file.columns.file_name == AudioFile.name).join(Equipment, AudioFile.sn == Equipment.serial_number).join(MonitoringStation).filter(MonitoringStation.project_id == project_id).group_by('station').group_by('date').order_by('date')
                df = pd.read_sql(per_day.statement, db.session.bind)
            fig = px.line(df, x='date', y='count', color='station', title='Daily count')
            fig.update_traces(mode='markers')
        except:
            fig = px.line()
        return fig


    @dashapp.callback(Output('hourly-graph', 'figure'), [Input('url', 'search'), Input('label-dropdown', 'value'), Input('min-prob', 'value'), Input('max-prob', 'value'), Input('iteration-dropdown', 'value'), Input('daily-graph', 'clickData')])
    def update_hourly_graph(query, selected_label_id, min_prob, max_prob, selected_iteration_id, clickData):
        try:
            query_dict = parse_qs(query[1:])
            project_id = query_dict['project'][0]
            selected_date = clickData['points'][0]['x']
            with dashapp.server.app_context():
                per_file = db.session.query(ModelOutput.file_name, func.count(ModelOutput.id).label('count')).filter(ModelOutput.iteration_id == selected_iteration_id, ModelOutput.label_id == selected_label_id, ModelOutput.probability >= float(min_prob), ModelOutput.probability <= float(max_prob)).group_by(ModelOutput.file_name).subquery()
                per_hour = db.session.query(MonitoringStation.name.label('station'), func.sum(per_file.columns.count).label('count'), func.date(AudioFile.timestamp).label('date'), func.extract('hour', AudioFile.timestamp).label('hour')).join(AudioFile, per_file.columns.file_name == AudioFile.name).join(Equipment, AudioFile.sn == Equipment.serial_number).join(MonitoringStation).group_by('station').group_by('date').group_by('hour').filter(MonitoringStation.project_id == project_id, func.date(AudioFile.timestamp) == selected_date).order_by('hour')
                df = pd.read_sql(per_hour.statement, db.session.bind)
            fig = px.line(df, x='hour', y='count', color='station', title='Hourly count for '+selected_date)
            fig.update_traces(mode='markers')
        except:
            fig = px.line()
        return fig

