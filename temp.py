import os 
import yt_dlp

def download_video(url, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

    ydl_opts = {
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

# # Example Usage (REMOVE THIS)
Youtube_video_url = "https://youtu.be/6ya5KMhR4ug?si=jx-ySNTmOUCtMlhi" 
# Directory is location where you want to save you video
directory = "temp"
download_video(Youtube_video_url, directory)