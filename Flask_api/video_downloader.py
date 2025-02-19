import os 
import yt_dlp

def download_video(url, format_id, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

    ydl_opts = {
        'format': format_id,
        # 'proxy': 'http://203.115.101.53:5000',
        'cookiefile': 'cookies.txt',
        'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, '', info['title'], info.get('thumbnail', '')
    except Exception as e:
        print(f"Error downloading video: {str(e)}")  # Debug print
        return 'Something Went Wrong', str(e), '', ''