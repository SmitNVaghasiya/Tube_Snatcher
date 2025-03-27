import yt_dlp
from concurrent.futures import ThreadPoolExecutor

def fetch_video_info(url, selected_format):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': False,
    }

    def fetch_single_video_info(video_url, ydl_opts):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                print(f"Fetched info for {video_url}: {info.get('title', 'Untitled')}")
                return info
        except Exception as e:
            print(f"Error fetching info for {video_url}: {str(e)}")
            return None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:  # Playlist detected
                videos = []
                batch_size = 5  # Process 5 videos at a time
                entries = info['entries']

                # Initial playlist metadata
                result = {
                    'type': 'playlist',
                    'title': info.get('title', 'Playlist'),
                    'thumbnail': info.get('thumbnails', [{}])[-1].get('url', ''),
                    'videos': videos
                }
                print(f"Playlist detected: {result['title']} with {len(entries)} videos")

                # Process videos in batches using ThreadPoolExecutor
                with ThreadPoolExecutor() as executor:
                    for i in range(0, len(entries), batch_size):
                        batch = entries[i:i + batch_size]
                        batch_urls = [entry.get('url', entry.get('webpage_url')) for entry in batch if entry.get('url', entry.get('webpage_url'))]
                        video_infos = list(executor.map(lambda url: fetch_single_video_info(url, ydl_opts), batch_urls))
                        for video_info in video_infos:
                            if video_info:  # Only add if info was successfully fetched
                                formats = []
                                for fmt in video_info.get('formats', []):
                                    if 'storyboard' in fmt.get('format_note', '').lower():  # Skip storyboard formats
                                        continue
                                    resolution = f"{fmt.get('width')}x{fmt.get('height')}" if fmt.get('width') and fmt.get('height') else 'Audio Only'
                                    filesize_str = f"{round(fmt.get('filesize', 0) / (1024 * 1024), 2)} MB" if fmt.get('filesize') else "Size Unknown"
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
                print(f"Processed {len(videos)} videos for playlist")
                return result
            else:  # Single video
                ydl_opts_single = {
                    'format': 'bestaudio/best' if selected_format == 'mp3' else 'bestvideo+bestaudio/best',
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True
                }
                info = fetch_single_video_info(url, ydl_opts_single)
                if not info:
                    print("Failed to fetch single video info")
                    return None
                formats = info.get('formats', [])
                grouped_formats = {}
                for fmt in formats:
                    if 'storyboard' in fmt.get('format_note', '').lower():  # Skip storyboard formats
                        continue
                    resolution = f"{fmt.get('width')}x{fmt.get('height')}" if fmt.get('width') and fmt.get('height') else 'Audio Only'
                    if resolution not in grouped_formats:
                        grouped_formats[resolution] = []
                    grouped_formats[resolution].append(fmt)
                available_formats = []
                for res, fmt_list in grouped_formats.items():
                    best_fmt = max(fmt_list, key=lambda x: x.get('filesize', 0) or 0)
                    filesize_str = f"{round(best_fmt.get('filesize', 0) / (1024 * 1024), 2)} MB" if best_fmt.get('filesize') else "Size Unknown"
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
                print(f"Single video fetched: {result['title']} with {len(available_formats)} formats")
                return result
    except Exception as e:
        print(f"Error fetching video info for {url}: {str(e)}")
        return None