def _video_format(max_height: int) -> str:
    """
    Кнопки качества (/144 ... /1080) задают ВЕРХНЮЮ границу: берём лучший
    доступный поток не выше max_height.

    Первым идёт h264 (vcodec^=avc1) + m4a: только такая связка играется
    штатным плеером Telegram. Фильтр именно по кодек, а не по [ext=mp4] -
    YouTube отдаёт AV1 тоже в mp4-контейнере (itag 394-400), а Telegram
    его не декодирует. Если h264 на этой высоте нет (современные ролики
    дают 1080p только в AV1) - берём лучший mp4 ниже, и лишь в крайнем
    случае webm, который склеивается в mp4 через merge_output_format.
    """
    return (
        f'bestvideo[height<={max_height}][vcodec^=avc1]+bestaudio[acodec^=mp4a]'
        f'/best[height<={max_height}][vcodec^=avc1]'
        f'/bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]'
    )


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
        'format': _video_format(144),
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '240': {
        'format': _video_format(240),
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '360': {
        'format': _video_format(360),
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '480': {
        'format': _video_format(480),
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '720': {
        'format': _video_format(720),
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '1080': {
        'format': _video_format(1080),
        'extension': 'mp4',
        'send_method': 'send_video'
    },
}
