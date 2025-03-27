import time
import os
import yt_dlp

def download_video(url, format_id_or_height, directory, format_type):
    start_time = time.time()
    print(f"Download started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    ydl_opts = {
        'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }

    if format_type == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio',
            'extractaudio': True,
            'audioformat': 'mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        if format_id_or_height == 'best':
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        elif format_id_or_height:
            if format_id_or_height.isdigit():
                ydl_opts['format'] = f"bestvideo[height<={format_id_or_height}]+bestaudio/best[height<={format_id_or_height}]"
            else:
                ydl_opts['format'] = format_id_or_height
        ydl_opts.update({
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'keepvideo': False,  # Delete intermediate files
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return None, str(e), None, None

    end_time = time.time()
    duration = (end_time - start_time) / 60
    file_size = os.path.getsize(filename) / (1024 * 1024)
    print(f"Download finished at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    print(f"Time taken: {duration:.2f} minutes")
    print(f"File size: {file_size:.2f} MB")

    return filename, None, info.get('title', 'Untitled'), info.get('thumbnail', '')