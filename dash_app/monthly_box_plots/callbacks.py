from datetime import datetime as dt
import calendar
from dash import callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from sqlalchemy import func, extract, desc
from app import db
from app.models import ModelOutput, AudioFile, MonitoringStation, Label
from dash_app.util import get_q, get_breadcrumbs
from dash_app.callbacks import register_callbacks as register_filter_callbacks


def register_callbacks(dashapp):

    register_filter_callbacks(dashapp)


    @dashapp.callback(Output('breadcrumbs', 'items'), Input('url', 'search'))
    def update_breadcrumbs(query):
        items = get_breadcrumbs(query)
        items.append({'label': 'Box plots', 'active': True})
        return items


    @dashapp.callback(Output('monthly-grid', 'figure'), [Input('url', 'search'), Input('label-dropdown', 'value'), Input('min-prob', 'value'), Input('max-prob', 'value'), Input('start-hour', 'value'), Input('end-hour', 'value'), Input('iteration-dropdown', 'value')])
    def update_graph(query, selected_label_id, min_prob, max_prob, start_hour, end_hour, selected_iteration_id):
        try:
            if selected_label_id == None:
                raise
            project_id = get_q(query, 'project')
            with dashapp.server.app_context():
                label = Label.query.get(selected_label_id)
                stations = MonitoringStation.query.filter(MonitoringStation.project_id == project_id).order_by(MonitoringStation.elevation).all()
                per_file = db.session.query(ModelOutput.file_name, func.count(ModelOutput.id).label('count')).filter(ModelOutput.iteration_id == selected_iteration_id, ModelOutput.label_id == selected_label_id, ModelOutput.probability >= float(min_prob), ModelOutput.probability <= float(max_prob)).group_by(ModelOutput.file_name).subquery()
                per_day = db.session.query(MonitoringStation.id.label('station'), func.date(AudioFile.timestamp).label('date'), func.sum(per_file.columns.count).label('count')).join(AudioFile, per_file.columns.file_name == AudioFile.name).join(AudioFile.monitoring_station).filter(MonitoringStation.project_id == project_id, func.extract('hour', AudioFile.timestamp) >= start_hour, func.extract('hour', AudioFile.timestamp) <= end_hour).group_by('station').group_by('date').order_by('date')
                predictions_df = pd.read_sql_query(per_day.statement, db.session.bind, parse_dates=['date'])
                first_file_for_day = db.session.query(MonitoringStation.id.label('station'), func.min(AudioFile.id).label('first_file'), func.date(AudioFile.timestamp).label('date')).join(AudioFile.monitoring_station).filter(MonitoringStation.project_id == project_id).group_by('station').group_by('date').subquery()
                days_with_files = db.session.query(first_file_for_day.columns.station, func.extract('year', first_file_for_day.columns.date).label('year'), func.extract('month', first_file_for_day.columns.date).label('month'), func.count(first_file_for_day.columns.date).label('day_count')).group_by('station').group_by('year').group_by('month')
                files_df = pd.read_sql_query(days_with_files.statement, db.session.bind)
            start_date = dt(int(files_df['year'].min()), 1, 1)
            end_date = dt(int(files_df['year'].max()), 12, 31)
            days_df = pd.DataFrame({'date': pd.date_range(start=start_date, end=end_date)})
            stations_df = pd.DataFrame({'station': [station.id for station in stations]})
            days_df = days_df.merge(stations_df, how='cross')
            predictions_df = days_df.merge(predictions_df, how='left', on=['date', 'station'])
            predictions_df = predictions_df.fillna(0)
            predictions_df['year'] = predictions_df['date'].dt.year
            predictions_df['month'] = predictions_df['date'].dt.month
            by_year = predictions_df.groupby('year')
            years = [year for year, group in by_year]
            station_titles = [station.name + ' ({0} m)'.format(station.elevation) for station in stations]
            station_titles.append('Days with Data')
            fig = make_subplots(rows=len(stations)+1, cols=len(years), row_titles=station_titles, column_titles=years, y_title='Detections per day', shared_yaxes='rows')
            file_percentiles = pd.DataFrame()
            file_percentiles['quartile'] = [1.0, 0.75, 0.5, 0.25]
            file_percentiles['color'] = ['green', 'yellow', 'orange', 'red']
            file_percentiles['title'] = ['100-75%', '75-50%', '50-25%', '25-0%']
            # this useless bar graph is just so we have a legend
            for i in file_percentiles.index:
                fig.add_trace(go.Bar(x=[''], y=[file_percentiles.loc[i, 'quartile']], marker_color=file_percentiles.loc[i, 'color'], name=file_percentiles.loc[i, 'title'], legendgroup=file_percentiles.loc[i, 'title']), row=len(stations)+1, col=len(years))
            row = 1
            for station in stations:
                col = 1
                for year in years:
                    for month in range(1, 13):
                        filtered_df = predictions_df[(predictions_df['station'] == station.id) & (predictions_df['year'] == year) & (predictions_df['month'] == month)]
                        counts = filtered_df['count'] if not filtered_df['count'].empty else [0]
                        filtered_file_df = files_df[(files_df['station'] == station.id) & (files_df['year'] == year) & (files_df['month'] == month)]
                        days_with_data = filtered_file_df['day_count'].values[0] if not filtered_file_df['day_count'].empty else 0
                        days_in_month = calendar.monthrange(year, month)[1]
                        ratio = days_with_data / days_in_month
                        for i in file_percentiles.index:
                            if ratio <= file_percentiles.loc[i, 'quartile']:
                                color = file_percentiles.loc[i, 'color']
                        month_name = dt(1, int(month), 1).strftime("%B")
                        more_info = [{'date': filtered_df.loc[i, 'date'].date(), 'station_id': filtered_df.loc[i, 'station']} for i in filtered_df.index]
                        fig.add_trace(go.Box(y=counts, name=month_name, marker_color=color, boxmean='sd', legendgroup=file_percentiles.loc[i, 'title'], showlegend=False, customdata=more_info), row=row, col=col)
                    col = col + 1
                row = row + 1
            fig.update_layout(height=500*len(stations), legend_title_text='Days with Data', title_text=str(label))
            fig.update_yaxes(rangemode='tozero')
        except:
            fig = go.Figure()
            fig.update_layout(
                title='',
                annotations = [{
                    'text': 'Please select a label',
                    'showarrow': False,
                    'font': {'size': 28}
                }]
            )
        return fig


    @dashapp.callback(Output('more-info', 'is_open'), Output('more-info', 'title'), Output('month-link', 'href'), Output('verify-day', 'hidden'), Output('day-link', 'href'), Output('day-link', 'children'), Input('url', 'search'), Input('label-dropdown', 'value'), Input('min-prob', 'value'), Input('max-prob', 'value'), Input('start-hour', 'value'), Input('end-hour', 'value'), Input('iteration-dropdown', 'value'), Input('monthly-grid', 'clickData'))
    def open_more_info(query, selected_label_id, min_prob, max_prob, start_hour, end_hour, selected_iteration_id, click_data):
        title = ''
        month_url = ''
        hide_day = True
        day_url = ''
        day_text = ''
        if callback_context.triggered[0]['prop_id'] == 'monthly-grid.clickData':
            should_open = True
            project_id = get_q(query, 'project')
            station_id = click_data['points'][0]['customdata']['station_id']
            station = MonitoringStation.query.get(station_id)
            date_string = click_data['points'][0]['customdata']['date']
            date = dt.strptime(date_string, '%Y-%m-%d')
            month = date.strftime("%B %Y")
            title = '{station} ({elevation} m) - {month}'.format(station=station.name, elevation=station.elevation, month=month)
            start_date = dt(date.year, date.month, 1).strftime('%Y-%m-%d')
            end_date = dt(date.year, date.month, calendar.monthrange(date.year, date.month)[1]).strftime('%Y-%m-%d')
            month_url = '/ml/project/{project_id}?iteration={iteration_id}&label={label_id}&min_prob={min_prob}&max_prob={max_prob}&station={station_id}&start_date={start_date}&end_date={end_date}&start_hour={start_hour}&end_hour={end_hour}&sort=earliest'.format(project_id=project_id, iteration_id=selected_iteration_id, label_id=selected_label_id, min_prob=min_prob, max_prob=max_prob, station_id=station_id, start_date=start_date, end_date=end_date, start_hour=start_hour, end_hour=end_hour)
            if not 'hoverOnBox' in click_data['points'][0]:
                # outlier selected
                day_url = '/ml/project/{project_id}?iteration={iteration_id}&label={label_id}&min_prob={min_prob}&max_prob={max_prob}&station={station_id}&start_date={date}&end_date={date}&start_hour={start_hour}&end_hour={end_hour}&sort=earliest'.format(project_id=project_id, iteration_id=selected_iteration_id, label_id=selected_label_id, min_prob=min_prob, max_prob=max_prob, station_id=station_id, date=date_string, start_hour=start_hour, end_hour=end_hour)
                day_text = 'Verify selected outlier: {date}'.format(date=date_string)
                hide_day = False
        else:
           # close on filter changes
           should_open = False
        return should_open, title, month_url, hide_day, day_url, day_text
