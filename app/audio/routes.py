from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from sqlalchemy import extract
from app import db
from app.models import User, AudioFile, Equipment, MonitoringStation, Project
from app.audio import bp
from app.audio.forms import FilterForm
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
    wav_file = AudioFile.query.filter_by(name=file_name).first()
    size = wav_file.size
    byte1, byte2, length = get_byte_range(request, size)

    vfs = get_azure_vfs()
    with vfs.open(wav_file.path+'/'+wav_file.name) as f:
        f.seek(byte1)
        data = f.read(length)

    response = Response(data,
        206,
        mimetype='audio/x-wav',
        direct_passthrough=True)
    response.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, size))
    return response


@bp.route('/stream_file/<file_name>.<file_type>')
@login_required
def stream_compressed(file_name, file_type):
    wav_file = AudioFile.query.filter_by(name=file_name).first()

    vfs = get_azure_vfs()
    with vfs.open(wav_file.path+'/'+wav_file.name) as f:
        out_f, output_mime = compress_audio(f, file_type)

    size = sys.getsizeof(out_f)
    byte1, byte2, length = get_byte_range(request, size)
    out_f.seek(byte1)
    data = out_f.read(length)

    response = Response(data,
        206,
        mimetype=output_mime,
        direct_passthrough=True)
    response.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, size))
    return response


@bp.route('/stream_clip/<file_name>-<offset>.<file_type>')
@login_required
def stream_clip(file_name, offset, file_type):
    clip = get_clip(file_name, offset)
    out_f, output_mime = compress_audio(clip, file_type)
    response = Response(out_f.getvalue(), mimetype=output_mime)
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


@bp.route('/files', methods=['GET', 'POST'])
@bp.route('/files/project/<project_id>', methods=['GET', 'POST'])
@login_required
def list_files(project_id=None):
    filter_form = FilterForm()
    q = AudioFile.query
    fq = MonitoringStation.query

    if project_id:
        q = q.join(Equipment, AudioFile.sn == Equipment.serial_number).join(MonitoringStation).join(Project).filter(Project.id == project_id)
        fq = fq.join(Project).filter(Project.id == project_id)
    else:
        fq = fq.all()
    filter_form.select_station.query = fq

    if filter_form.validate_on_submit():
        page = 1
        station = filter_form.select_station.data.id if filter_form.select_station.data else None
        after = filter_form.after.data
        before = filter_form.before.data
        from_hour = filter_form.from_hour.data
        until_hour = filter_form.until_hour.data
    else:
        page = request.args.get('page', 1, type=int)
        station = request.args.get('station', type=int)
        after_str = request.args.get('after', type=str)
        after = datetime.strptime(after_str, '%Y-%m-%d').date() if after_str else None
        before_str = request.args.get('before', type=str)
        before = datetime.strptime(before_str, '%Y-%m-%d').date() if before_str else None
        from_hour = request.args.get('from', type=int)
        until_hour = request.args.get('until', type=int)

    if station:
        if not project_id:
            q = q.join(Equipment, AudioFile.sn == Equipment.serial_number).join(MonitoringStation)
        q = q.filter(MonitoringStation.id == station)
    if after: q = q.filter(AudioFile.timestamp >= after)
    if before: q = q.filter(AudioFile.timestamp <= before)
    if from_hour: q = q.filter(extract('hour', AudioFile.timestamp) >= from_hour)
    if until_hour: q = q.filter(extract('hour', AudioFile.timestamp) < until_hour)

    files = q.order_by(AudioFile.timestamp).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
    filters = {'station':station, 'after':after, 'before':before, 'from':from_hour, 'until':until_hour}
    return render_template('audio/file_list.html', title='Browse all wav files', files=files, filter_form=filter_form, filters=filters)


