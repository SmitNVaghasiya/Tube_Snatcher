import yt_dlp

def fetch_video_info(url, selected_format):
    ydl_opts = {
        'format': 'bestaudio/best' if selected_format == 'mp3' else 'bestvideo+bestaudio/best',
        'skip_download': True,  # This option skips the actual download
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            available_formats = []

            for fmt in formats:
                ext = fmt.get('ext', 'N/A')
                
                # Filter based on selected format:
                if selected_format == 'mp3':
                    if fmt.get('acodec') == 'none':  # skip if no audio codec
                        continue
                elif selected_format == 'mp4':
                    if fmt.get('vcodec') == 'none':  # skip if no video codec
                        continue

                # Determine filesize, if available:
                filesize_raw = fmt.get('filesize')
                if filesize_raw:
                    filesize_mb = round(filesize_raw / (1024 * 1024), 2)
                    if filesize_mb < 1024:
                        filesize_str = f"{filesize_mb} MB"
                    else:
                        filesize_str = f"{round(filesize_mb / 1024, 2)} GB"
                else:
                    filesize_str = None   # Do not show filesize if not available
                    filesize_raw = 0      # Use 0 for grouping comparisons

                format_info = {
                    'format_id': fmt.get('format_id'),
                    'resolution': f"{fmt.get('width')}x{fmt.get('height')}" if fmt.get('width') and fmt.get('height') else 'Audio Only',
                    'filesize': filesize_str,
                    'filesize_value': filesize_raw,  # raw numeric value for comparison
                    'format_note': fmt.get('format_note', 'N/A'),
                    'ext': ext  # File extension (mp4, webm, etc.)
                }
                available_formats.append(format_info)
            
            # Group formats by resolution and pick the one with the highest filesize_value.
            grouped_formats = {}
            for fmt in available_formats:
                res = fmt['resolution']
                if res in grouped_formats:
                    if fmt['filesize_value'] > grouped_formats[res]['filesize_value']:
                        grouped_formats[res] = fmt
                else:
                    grouped_formats[res] = fmt

            final_formats = list(grouped_formats.values())
            return info, final_formats
    except Exception as e:
        print(f"Error fetching video info: {str(e)}")
        return None, []

# Example Usage
video_url = "https://www.youtube.com/watch?v=example"  # Replace with an actual video URL
selected_format = "mp4"  # Use "mp3" for audio only
info, formats = fetch_video_info(video_url, selected_format)
for fmt in formats:
    # If filesize is None, you can choose not to display it in your UI.
    display_size = fmt['filesize'] if fmt['filesize'] else ""
    print(f"{fmt['format_note']}, {fmt['resolution']}, {display_size}")
