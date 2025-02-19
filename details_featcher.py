import yt_dlp

def fetch_video_info(url, selected_format):
    ydl_opts = {
        'format': 'bestaudio/best' if selected_format == 'mp3' else 'bestvideo+bestaudio/best',
        'cookiefile': 'cookies.txt',
        'skip_download': True,  # Only extract info, don't download
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                print("Error: Could not fetch video details.")
                return None, []

            formats = info.get('formats', [])
            available_formats = []

            for fmt in formats:
                ext = fmt.get('ext', 'N/A')

                # Filter formats based on user selection (mp3 or mp4)
                if selected_format == 'mp3' and fmt.get('acodec') == 'none':
                    continue  # Skip video-only formats for mp3 mode
                elif selected_format == 'mp4' and fmt.get('vcodec') == 'none':
                    continue  # Skip audio-only formats for mp4 mode

                # Handle File Size Display
                filesize_raw = fmt.get('filesize')  # Get raw filesize (can be None)
                if filesize_raw is not None:
                    filesize_mb = round(filesize_raw / (1024 * 1024), 2)
                    filesize_str = f"{filesize_mb} MB" if filesize_mb < 1024 else f"{round(filesize_mb / 1024, 2)} GB"
                else:
                    filesize_mb = 0  # Default for sorting
                    filesize_str = "Unknown"

                format_info = {
                    'format_id': fmt.get('format_id'),
                    'resolution': f"{fmt.get('width')}x{fmt.get('height')}" if fmt.get('width') and fmt.get('height') else 'Audio Only',
                    'filesize': filesize_str,
                    'filesize_value': filesize_mb,  # Ensure sorting works
                    'format_note': fmt.get('format_note', 'N/A'),
                    'ext': ext
                }
                available_formats.append(format_info)

            # Group formats by resolution, keeping the highest quality
            grouped_formats = {}
            for fmt in available_formats:
                res = fmt['resolution']
                if res in grouped_formats:
                    if fmt['filesize_value'] > grouped_formats[res]['filesize_value']:
                        grouped_formats[res] = fmt
                else:
                    grouped_formats[res] = fmt

            return info, list(grouped_formats.values())

    except Exception as e:
        print(f"Error fetching video info: {str(e)}")
        return None, []

# # Example Usage (REMOVE THIS)
# video_url = "https://www.youtube.com/watch?v=VALID_VIDEO_ID"  # Replace with an actual video URL
# selected_format = "mp4"
# info, formats = fetch_video_info(video_url, selected_format)

# for fmt in formats:
#     display_size = fmt['filesize'] if fmt['filesize'] else ""
#     print(f"{fmt['format_note']}, {fmt['resolution']}, {display_size}")
