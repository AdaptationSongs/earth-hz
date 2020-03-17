// Global variables
var current_offset = 0;


function playClip(wav_file, offset) {
    var audio = $('audio').get(0);
    if (audio.canPlayType('audio/ogg')) {
        $('audio').attr('src', '/stream_clip/'+wav_file+'-'+offset+'.ogg');
    } else {
        $('audio').attr('src', '/stream_clip/'+wav_file+'-'+offset+'.mp3');
    }
    audio.load();
    audio.play();
}


function playStream(wav_file) {
    var audio = $('audio').get(0);
// Weird stuff happens when seeking in Ogg files - variable bitrate?
//    if (audio.canPlayType('audio/ogg')) {
//        $('audio').attr('src', '/stream_file/'+wav_file+'.ogg');
//    } else {
//        $('audio').attr('src', '/stream_file/'+wav_file+'.mp3');
//    }
    $('audio').attr('src', '/stream_file/'+wav_file+'.mp3');
    $('#current-file').text(wav_file);
    $('#replay-btn').removeClass('disabled');
    $('#label-btn').removeClass('disabled').attr('href', '/clip/'+wav_file+'/0');
    $('#spec-img').removeClass('d-none').attr('src', '/spectrogram/'+wav_file+'-0.png');

    audio.load();
    audio.play();
    $(audio).off('timeupdate.full');
    $(audio).on('timeupdate.full', function() {
        var new_offset = Math.floor(audio.currentTime / 5) * 5;
        if (new_offset != current_offset) {
            current_offset = new_offset;
            $('#current-offset').text('+'+current_offset+' sec');
            $('#replay-btn').click(function() {
                playSelection(current_offset, 5);
            });
            $('#label-btn').attr('href', '/clip/'+wav_file+'/'+current_offset);
            $('#spec-img').attr('src', '/spectrogram/'+wav_file+'-'+current_offset+'.png');
        }
    });
}


function playSelection(start, duration) {
    var audio = $('audio').get(0);
    var end_float = parseFloat(start) + parseFloat(duration);
    var end = end_float.toFixed(5);
    audio.pause();
    audio.currentTime = start;
    audio.play();
    $(audio).on('timeupdate.clip', function() {
        if (audio.currentTime >= end) {
            audio.pause();
            audio.currentTime = end - 0.01;
            $(audio).off('timeupdate.clip');
        } 
    });
}
