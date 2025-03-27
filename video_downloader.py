import os
import yt_dlp

def download_video(url, format_id, directory, file_type):
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Set format options based on file type
    if file_type == "mp3":
        ydl_opts = {
            'format': format_id,  # Use the exact format selected by the user
            'extract_audio': True,
            'audio_format': 'mp3',
            'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
        }
    else:  # MP4 Download (with best video + best audio)
        ydl_opts = {
            # 'format': f"{format_id}+bestaudio/best",  # Use selected video + best audio
            # 'merge_output_format': 'mp4',  # Merge audio and video into mp4 format
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
