import os 
import yt_dlp

def download_video(url, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

    ydl_opts = {
        'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',  # Select highest quality video and audio
        'merge_output_format': 'mp4',  # Ensure output is in mp4 format
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, '', info['title'], info.get('thumbnail', '')
    except Exception as e:
        print(f"Error downloading video: {str(e)}")  # Debug print
        return 'Something Went Wrong', str(e), '', ''

# Example Usage
Youtube_video_url = "https://youtu.be/7kBUAZsrlXc?si=OGrFNjyUFVwp1oKN&t=3029"
directory = "temp"
download_video(Youtube_video_url, directory)