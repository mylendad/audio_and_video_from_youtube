FORMATS = {
    'mp3': {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'extension': 'mp3',
        'send_method': 'send_audio'
    },
    '144': {
        'format': 'bestvideo[height<=144]+bestaudio/best[height<=144]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '240': {
        'format': 'bestvideo[height<=240]+bestaudio/best[height<=240]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '360': {
        'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '480': {
        'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '720': {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '1080': {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
}
