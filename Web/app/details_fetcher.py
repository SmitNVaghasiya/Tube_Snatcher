# app/details_fetcher.py
import yt_dlp
from concurrent.futures import ThreadPoolExecutor

def fetch_video_info(url, selected_format):
    # Updated options to fetch all video formats with file size information
    ydl_opts = {
        'quiet': True,  # Suppress console output, including format table
        'no_warnings': True,  # Suppress warnings
        'noplaylist': False,  # Handle playlists
        'format': 'bestvideo+bestaudio/best' if selected_format != 'mp3' else 'bestaudio/best',  # Request video and audio formats
        'merge_output_format': 'mp4' if selected_format != 'mp3' else None,  # Ensure MP4 for video, none for MP3
        'get_filesize': True,  # Request file size
        'dump_single_json': False,  # Avoid single JSON dump for detailed format list
        # Removed 'listformats': True to prevent format table output in cmd
    }

    def fetch_single_video_info(video_url, ydl_opts):
        """Helper function to fetch info for a single video."""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                # Debug: Print raw format data to verify file size retrieval
                print(f"Raw format data for {video_url}:")
                # print(f"Raw format data for {video_url}: {info.get('formats', [])}")
                return info
        except Exception as e:
            print(f"Error fetching info for {video_url}: {str(e)}")
            return None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:  # Playlist detected
                videos = []
                batch_size = 5  # Process in batches for efficiency
                entries = info['entries']
                result = {
                    'type': 'playlist',
                    'title': info.get('title', 'Playlist'),
                    'thumbnail': info.get('thumbnails', [{}])[-1].get('url', ''),
                    'videos': videos
                }

                with ThreadPoolExecutor() as executor:
                    for i in range(0, len(entries), batch_size):
                        batch = entries[i:i + batch_size]
                        batch_urls = [entry.get('url', entry.get('webpage_url')) for entry in batch if entry.get('url', entry.get('webpage_url'))]
                        video_infos = list(executor.map(lambda url: fetch_single_video_info(url, ydl_opts), batch_urls))
                        for video_info in video_infos:
                            if video_info:
                                formats = []
                                for fmt in video_info.get('formats', []):
                                    # Skip storyboards or irrelevant formats
                                    if 'storyboard' in fmt.get('format_note', '').lower():
                                        continue
                                    width = fmt.get('width')
                                    height = fmt.get('height')
                                    resolution = f"{width}x{height}" if width and height else 'Audio Only' if fmt.get('vcodec') == 'none' else 'N/A'
                                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                                    if not filesize and width and height:
                                        filesize = estimate_filesize(width, height)  # Fallback estimation
                                    filesize_str = f"{round(filesize / (1024 * 1024), 2)} MB" if filesize else "Size Unknown"
                                    format_info = {
                                        'format_id': fmt.get('format_id'),
                                        'resolution': resolution,
                                        'filesize': filesize_str,
                                        'format_note': fmt.get('format_note', 'N/A'),
                                        'ext': fmt.get('ext', 'N/A')
                                    }
                                    formats.append(format_info)
                                videos.append({
                                    'title': video_info.get('title', 'Untitled'),
                                    'url': video_info.get('webpage_url', video_info.get('url')),
                                    'thumbnail': video_info.get('thumbnail', ''),
                                    'duration': video_info.get('duration', 0),
                                    'formats': formats
                                })
                return result
            else:  # Single video
                ydl_opts_single = {
                    'format': 'bestaudio/best' if selected_format == 'mp3' else 'bestvideo+bestaudio/best',
                    'quiet': True,  # Suppress console output
                    'no_warnings': True,
                    'noplaylist': True,
                    'get_filesize': True,
                    # Removed 'listformats': True to prevent format table output in cmd
                }
                info = fetch_single_video_info(url, ydl_opts_single)
                if not info:
                    return None
                formats = info.get('formats', [])
                grouped_formats = {}
                for fmt in formats:
                    if 'storyboard' in fmt.get('format_note', '').lower():
                        continue
                    width = fmt.get('width')
                    height = fmt.get('height')
                    resolution = f"{width}x{height}" if width and height else 'Audio Only' if fmt.get('vcodec') == 'none' else 'N/A'
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    if not filesize and width and height:
                        filesize = estimate_filesize(width, height)  # Fallback estimation
                    filesize_str = f"{round(filesize / (1024 * 1024), 2)} MB" if filesize else "Size Unknown"
                    if resolution not in grouped_formats:
                        grouped_formats[resolution] = []
                    grouped_formats[resolution].append(fmt)
                available_formats = []
                for res, fmt_list in grouped_formats.items():
                    best_fmt = max(fmt_list, key=lambda x: x.get('filesize', 0) or x.get('filesize_approx', 0) or 0)
                    filesize = best_fmt.get('filesize') or best_fmt.get('filesize_approx', 0)
                    if not filesize and best_fmt.get('width') and best_fmt.get('height'):
                        filesize = estimate_filesize(best_fmt.get('width'), best_fmt.get('height'))
                    filesize_str = f"{round(filesize / (1024 * 1024), 2)} MB" if filesize else "Size Unknown"
                    format_info = {
                        'format_id': best_fmt.get('format_id'),
                        'resolution': res,
                        'filesize': filesize_str,
                        'format_note': best_fmt.get('format_note', 'N/A'),
                        'ext': best_fmt.get('ext', 'N/A')
                    }
                    available_formats.append(format_info)
                result = {
                    'type': 'video',
                    'title': info.get('title', 'No title available'),
                    'thumbnail': info.get('thumbnail', ''),
                    'formats': available_formats
                }
                return result
    except Exception as e:
        print(f"Error fetching video info for {url}: {str(e)}")
        return None

def estimate_filesize(width, height):
    """Estimate file size based on resolution (rough approximation)."""
    resolution_area = width * height
    # Rough estimation: ~1 MB per 100,000 pixels for typical video compression
    estimated_size = (resolution_area / 100000) * 1024 * 1024  # In bytes
    return estimated_size