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
    audio.load();
    audio.play();
}


function playFile(path) {
    $('audio').attr('src', path);
    var audio = $('audio').get(0);
    audio.load();
    audio.play();
}

function playSelection(file_name, start, duration) {
    $('audio').attr('src', '/wav/'+file_name);                                       
    var audio = $('audio').get(0);
    var end_float = parseFloat(start) + parseFloat(duration);
    var end = end_float.toFixed(5);
    audio.pause();
    audio.currentTime = start;
    audio.play();
    $(audio).on('timeupdate', function() {
        if (audio.currentTime >= end) {
            audio.pause();
            $(audio).off('timeupdate');
        } 
    });
}
