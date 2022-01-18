from datetime import datetime as dt
from urllib.parse import parse_qs
from itertools import cycle
import pandas_datareader as pdr
from dash import callback_context
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate
import plotly_express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import func, extract, desc
from app import db
from app.models import ModelOutput, AudioFile, Equipment, MonitoringStation, Project, ProjectLabel, Label, MLModel, ModelIteration, ModelLabel, StatusEnum


def get_project_id(query):
    query_dict = parse_qs(query[1:])
    return query_dict['project'][0]


def get_station_colors(project_id):
    stations = MonitoringStation.query.filter(MonitoringStation.project_id == project_id).all()
    station_names = [s.name for s in stations]
    color_map = dict(zip(station_names, cycle(px.colors.qualitative.Plotly)))
    return color_map


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
            project_id = get_project_id(query)
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


    @dashapp.callback(Output('daily-graph', 'figure'), [Input('url', 'search'), Input('label-dropdown', 'value'), Input('min-prob', 'value'), Input('max-prob', 'value'), Input('start-hour', 'value'), Input('end-hour', 'value'), Input('iteration-dropdown', 'value')])
    def update_graph(query, selected_label_id, min_prob, max_prob, start_hour, end_hour, selected_iteration_id):
        try:
            if selected_label_id == None:
                raise
            project_id = get_project_id(query)
            with dashapp.server.app_context():
                per_file = db.session.query(ModelOutput.file_name, func.count(ModelOutput.id).label('count')).filter(ModelOutput.iteration_id == selected_iteration_id, ModelOutput.label_id == selected_label_id, ModelOutput.probability >= float(min_prob), ModelOutput.probability <= float(max_prob)).group_by(ModelOutput.file_name).subquery()
                per_day = db.session.query(func.min(MonitoringStation.id).label('station_id'), MonitoringStation.name.label('station'), func.sum(per_file.columns.count).label('count'), func.date(AudioFile.timestamp).label('date')).join(AudioFile, per_file.columns.file_name == AudioFile.name).join(Equipment, AudioFile.sn == Equipment.serial_number).join(MonitoringStation).filter(MonitoringStation.project_id == project_id, func.extract('hour', AudioFile.timestamp) >= start_hour, func.extract('hour', AudioFile.timestamp) <= end_hour,).group_by('station').group_by('date').order_by('date')
                df = pd.read_sql(per_day.statement, db.session.bind)
                station_colors = get_station_colors(project_id)
                label = Label.query.get(selected_label_id)
            fig = px.line(df, x='date', y='count', custom_data=['station_id', 'station'], color='station', color_discrete_map=station_colors, title='Daily count for {label} {start}:00-{end}:59'.format(label=label, start=start_hour, end=end_hour))
            fig.update_traces(mode='markers')
        except:
            fig = go.Figure()
            fig.update_layout(
                title='Daily count',
                annotations = [{
                    'text': 'Please select a label',
                    'showarrow': False,
                    'font': {'size': 28}
                }]
            )
        return fig


    @dashapp.callback(Output('hourly-graph', 'figure'), [Input('url', 'search'), Input('label-dropdown', 'value'), Input('min-prob', 'value'), Input('max-prob', 'value'), Input('iteration-dropdown', 'value'), Input('daily-graph', 'clickData')])
    def update_hourly_graph(query, selected_label_id, min_prob, max_prob, selected_iteration_id, clickData):
        try:
            project_id = get_project_id(query)
            selected_date = clickData['points'][0]['x']
            with dashapp.server.app_context():
                per_file = db.session.query(ModelOutput.file_name, func.count(ModelOutput.id).label('count')).filter(ModelOutput.iteration_id == selected_iteration_id, ModelOutput.label_id == selected_label_id, ModelOutput.probability >= float(min_prob), ModelOutput.probability <= float(max_prob)).group_by(ModelOutput.file_name).subquery()
                per_hour = db.session.query(func.min(MonitoringStation.id).label('station_id'), MonitoringStation.name.label('station'), func.sum(per_file.columns.count).label('count'), func.date(AudioFile.timestamp).label('date'), func.extract('hour', AudioFile.timestamp).label('hour')).join(AudioFile, per_file.columns.file_name == AudioFile.name).join(Equipment, AudioFile.sn == Equipment.serial_number).join(MonitoringStation).group_by('station').group_by('date').group_by('hour').filter(MonitoringStation.project_id == project_id, func.date(AudioFile.timestamp) == selected_date).order_by('hour')
                df = pd.read_sql(per_hour.statement, db.session.bind)
                station_colors = get_station_colors(project_id)
                label = Label.query.get(selected_label_id)
            fig = px.line(df, x='hour', y='count', custom_data=['station_id', 'station'], color='station', color_discrete_map=station_colors, title='Hourly count for {label} on {date}'.format(label=label, date=selected_date))
            fig.update_traces(mode='markers')
        except:
            fig = go.Figure()
            fig.update_layout(
                title='Hourly count',
                annotations = [{
                    'text': 'Select a day',
                    'showarrow': False,
                    'font': {'size': 28}
                }]
            )
        return fig


    @dashapp.callback([Output('verify-link', 'href'), Output('verify-link', 'children')], [Input('url', 'search'), Input('label-dropdown', 'value'), Input('min-prob', 'value'), Input('max-prob', 'value'), Input('iteration-dropdown', 'value'), Input('daily-graph', 'clickData'), Input('hourly-graph', 'clickData')])
    def update_verify_link_hour(query, selected_label_id, min_prob, max_prob, selected_iteration_id, daily_click, hourly_click):
        try:
            project_id = get_project_id(query)
            selected_date = daily_click['points'][0]['x']
            if callback_context.triggered[0]['prop_id'] == 'hourly-graph.clickData':
                selected_hour = hourly_click['points'][0]['x']
                station_id = hourly_click['points'][0]['customdata'][0]
                station_name = hourly_click['points'][0]['customdata'][1]
            else:
                selected_hour = None
                station_id = daily_click['points'][0]['customdata'][0]
                station_name = daily_click['points'][0]['customdata'][1]
            url = '/ml/project/{project_id}?iteration={iteration_id}&label={label_id}&min_prob={min_prob}&max_prob={max_prob}&station={station_id}&start_date={date}&end_date={date}&start_hour={hour}&end_hour={hour}&sort=earliest'.format(project_id=project_id, iteration_id=selected_iteration_id, label_id=selected_label_id, min_prob=min_prob, max_prob=max_prob, station_id=station_id, date=selected_date, hour=selected_hour)
            if selected_hour is not None:
                formatted_hour = str(selected_hour) + ':00-' + str(selected_hour + 1) + ':00'
            else:
                formatted_hour = ''
            label = Label.query.get(selected_label_id)
            link_text = 'Verify results for {label} on {date} at {station} {hour}'.format(label=label, date=selected_date, hour=formatted_hour, station=station_name)
        except:
            url='#'
            link_text=''
        return url, link_text


    @dashapp.callback(Output('file-graph', 'figure'), [Input('url', 'search')])
    def update_file_graph(query):
        try:
            project_id = get_project_id(query)
            with dashapp.server.app_context():
                project_files = AudioFile.query.join(Equipment, AudioFile.sn == Equipment.serial_number).join(MonitoringStation).filter(MonitoringStation.project_id == project_id).with_entities(AudioFile.size, AudioFile.timestamp, MonitoringStation.name.label('station')).subquery()
                bytes_per_day = db.session.query(func.sum(project_files.c.size).label('bytes'), func.date(project_files.c.timestamp).label('date'), project_files.c.station).group_by('station').group_by('date').order_by('date')
                df = pd.read_sql(bytes_per_day.statement, db.session.bind)
                df['MB'] = df['bytes'] / (1024 * 1024)
                station_colors = get_station_colors(project_id)
            fig = px.line(df, x='date', y='MB', color='station', color_discrete_map=station_colors, title='Data recorded per day')
            fig.update_traces(mode='markers')
            fig.update_layout(hovermode='x')
        except:
            fig = go.Figure()
            fig.update_layout(
                title='Data recorded per day',
                annotations = [{
                    'text': 'Loading...',
                    'showarrow': False,
                    'font': {'size': 28}
                }]
            )
        return fig


    @dashapp.callback(Output('hourly-file-graph', 'figure'), [Input('url', 'search'), Input('file-graph', 'clickData'), Input('daily-graph', 'clickData')])
    def update_detailed_file_graph(query, file_click_data, daily_click_data):
        try:
            project_id = get_project_id(query)
            if callback_context.triggered[0]['prop_id'] == 'file-graph.clickData':
                selected_date = file_click_data['points'][0]['x']
            if callback_context.triggered[0]['prop_id'] == 'daily-graph.clickData':
                selected_date = daily_click_data['points'][0]['x']
            with dashapp.server.app_context():
                project_files = AudioFile.query.join(Equipment, AudioFile.sn == Equipment.serial_number).join(MonitoringStation).filter(MonitoringStation.project_id == project_id, func.date(AudioFile.timestamp) == selected_date).with_entities(AudioFile.size, AudioFile.timestamp, MonitoringStation.name.label('station')).subquery()
                bytes_per_hour = db.session.query(func.sum(project_files.c.size).label('bytes'), func.extract('hour', project_files.c.timestamp).label('hour'), project_files.c.station).group_by('station').group_by('hour').order_by('hour')
                df = pd.read_sql(bytes_per_hour.statement, db.session.bind)
                df['MB'] = df['bytes'] / 1024 / 1024
                station_colors = get_station_colors(project_id)
            fig = px.line(df, x='hour', y='MB', color='station', color_discrete_map=station_colors, title='Data recorded per hour on '+selected_date)
            fig.update_traces(mode='markers')
            fig.update_layout(hovermode='x')
        except:
            fig = go.Figure()
            fig.update_layout(
                title='Data recorded per hour',
                annotations = [{
                    'text': 'Select a day',
                    'showarrow': False,
                    'font': {'size': 28}
                }]
            )
        return fig

