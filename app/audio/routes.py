from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from sqlalchemy import extract
from app import db
from app.models import User, AudioFile, MonitoringStation, Project
from app.audio import bp
from app.audio.forms import FilterForm
from app.user.permissions import ListenPermission
import io
import sys
import re
from datetime import datetime, date
from app.audio.azure_datalake import get_azure_vfs
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import librosa
import librosa.display as lrd
import soundfile as sf
from pydub import AudioSegment


def get_clip(file_name, offset):
    window_size = current_app.config['CLIP_SECS']
    wav_file = AudioFile.query.filter_by(name=file_name).first()
    fpath = wav_file.path + '/' + wav_file.name
    vfs = get_azure_vfs()
    with vfs.open(fpath) as f:
        with sf.SoundFile(f) as sf_desc:
            sr = sf_desc.samplerate
            pos = int(float(offset) * sr)
            sf_desc.seek(pos)
            frame_duration = int(window_size * sr)
            clip_data = sf_desc.read(frames=frame_duration)

    tmp_f = io.BytesIO()
    sf.write(tmp_f, clip_data, sr, format='WAV')
    tmp_f.seek(0)
    return tmp_f


def get_byte_range(req, full_size):
    byte1, byte2 = 0, None
    range_header = req.headers.get('Range', None)
    if (range_header):
        m = re.search('(\d+)-(\d*)', range_header)
        g = m.groups()
        if g[0]: byte1 = int(g[0])
        if g[1]: byte2 = int(g[1])
    length = full_size - byte1
    if byte2 is not None:
        length = byte2 + 1 - byte1
    return byte1, byte2, length


def compress_audio(file_handle, file_type):
    if (file_type == 'ogg'):
        output_format = 'ogg'
        output_mime = 'audio/ogg'
    else:
        output_format = 'mp3'
        output_mime = 'audio/mpeg'
    segment = AudioSegment.from_file(file_handle, format='wav')
    tmp_f = io.BytesIO()
    segment.export(tmp_f, output_format)
    return tmp_f, output_mime


# Partial content support for audio seeking 
@bp.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response


@bp.route('/wav/<file_name>')
@login_required
def stream_wav(file_name):
    permission = ListenPermission(file_name)
    if permission.can():
        wav_file = AudioFile.query.filter_by(name=file_name).first()
        size = wav_file.size
        byte1, byte2, length = get_byte_range(request, size)
        vfs = get_azure_vfs()
        with vfs.open(wav_file.path+'/'+wav_file.name) as f:
            f.seek(byte1)
            data = f.read(length)
        response = Response(data, 206, mimetype='audio/x-wav', direct_passthrough=True)
        response.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, size))
    else:
        response = Response('Restricted audio', 403)
    return response


@bp.route('/stream_file/<file_name>.<file_type>')
@login_required
def stream_compressed(file_name, file_type):
    permission = ListenPermission(file_name)
    if permission.can():
        wav_file = AudioFile.query.filter_by(name=file_name).first()
        vfs = get_azure_vfs()
        with vfs.open(wav_file.path+'/'+wav_file.name) as f:
            out_f, output_mime = compress_audio(f, file_type)
        size = sys.getsizeof(out_f)
        byte1, byte2, length = get_byte_range(request, size)
        out_f.seek(byte1)
        data = out_f.read(length)
        response = Response(data, 206, mimetype=output_mime, direct_passthrough=True)
        response.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, size))
    else:
        response = Response('Restricted audio', 403) 
    return response


@bp.route('/stream_clip/<file_name>-<offset>.<file_type>')
@login_required
def stream_clip(file_name, offset, file_type):
    permission = ListenPermission(file_name)
    if permission.can():
        clip = get_clip(file_name, offset)
        out_f, output_mime = compress_audio(clip, file_type)
        response = Response(out_f.getvalue(), mimetype=output_mime)
    else:
        response = Response('Restricted audio', 403)
    return response


@bp.route('/spectrogram/<file_name>-<offset>.png')
@login_required
def spectro(file_name, offset):
    clip = get_clip(file_name, offset)
    y, sr = librosa.load(clip)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    S_dB = librosa.power_to_db(S, ref=np.max)
    fig = Figure()
    fig.set_dpi(60)
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(1,1,1)
    lrd.specshow(S_dB, ax=ax, x_axis='time', y_axis='mel', sr=sr, fmax=8000)
    fig.colorbar(ax.collections[0], format='%+2.0f dB')
    out_f = io.BytesIO()
    canvas.print_png(out_f)
    response = Response(out_f.getvalue(), mimetype='image/png')
    return response


@bp.route('/files')
@bp.route('/files/project/<project_id>')
@login_required
def list_files(project_id=None):
    page = request.args.get('page', 1, type=int)
    filter_form = FilterForm(request.args, meta={'csrf': False})
    q = AudioFile.query.join(AudioFile.monitoring_station)
    fq = MonitoringStation.query
    if project_id:
        q = q.filter(MonitoringStation.project_id == project_id)
        fq = fq.filter(MonitoringStation.project_id == project_id)
        project = Project.query.get(project_id)
    else:
        fq = fq.all()
        project = None
    filter_form.select_station.query = fq
    if filter_form.validate():
        if filter_form.select_station.data:
            q = q.filter(MonitoringStation.id == filter_form.select_station.data.id)
        if filter_form.after.data:
            q = q.filter(AudioFile.timestamp >= filter_form.after.data)
        if filter_form.before.data:
            q = q.filter(AudioFile.timestamp <= filter_form.before.data)
        if filter_form.from_hour.data:
            q = q.filter(extract('hour', AudioFile.timestamp) >= filter_form.from_hour.data)
        if filter_form.until_hour.data:
            q = q.filter(extract('hour', AudioFile.timestamp) < filter_form.until_hour.data) 
    files = q.order_by(AudioFile.timestamp).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
    return render_template('audio/file_list.html', title='Browse all wav files', project=project, files=files, filter_form=filter_form)


@bp.route('/audio/_get_date_range')
@bp.route('/audio/_get_date_range/<project_id>')
def _get_date_range(project_id=None):
    station_id = request.args.get('station', type=int)
    q = AudioFile.query.join(AudioFile.monitoring_station)
    if project_id:
        q = q.filter(MonitoringStation.project_id == project_id)
    if station_id:
        q = q.filter(MonitoringStation.id == station_id)
    first_file = q.order_by(AudioFile.timestamp.asc()).first()
    first_date = datetime.date(first_file.timestamp) if first_file else None
    last_file = q.order_by(AudioFile.timestamp.desc()).first()
    last_date = datetime.date(last_file.timestamp) if last_file else None
    date_range = {'first': first_date, 'last': last_date}
    return jsonify(date_range)

