import yt_dlp
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

async def fetch_video_info(url, selected_format):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': False,
    }

    # Semaphore to limit concurrent tasks to 5
    semaphore = asyncio.Semaphore(5)

    async def fetch_single_video_info(video_url, ydl_opts):
        async with semaphore:  # Limit concurrent tasks
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                try:
                    info = await loop.run_in_executor(pool, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(video_url, download=False))
                    return info
                except Exception as e:
                    print(f"Error fetching info for {video_url}: {str(e)}")
                    return None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:  # Playlist detected
                videos = []
                tasks = []
                for entry in info['entries']:
                    video_url = entry.get('url', entry.get('webpage_url'))
                    if video_url:
                        tasks.append(fetch_single_video_info(video_url, ydl_opts))
                video_infos = await asyncio.gather(*tasks)
                for video_info in video_infos:
                    if video_info:  # Only add if info was successfully fetched
                        videos.append({
                            'title': video_info.get('title', 'Untitled'),
                            'url': video_info.get('webpage_url', video_info.get('url')),
                            'thumbnail': video_info.get('thumbnail', ''),
                            'duration': video_info.get('duration', 0)
                        })
                return {
                    'type': 'playlist',
                    'title': info.get('title', 'Playlist'),
                    'thumbnail': info.get('thumbnails', [{}])[-1].get('url', ''),
                    'videos': videos
                }
            else:  # Single video
                ydl_opts_single = {
                    'format': 'bestaudio/best' if selected_format == 'mp3' else 'bestvideo+bestaudio/best',
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True
                }
                info = await fetch_single_video_info(url, ydl_opts_single)
                if not info:
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
                return {
                    'type': 'video',
                    'title': info.get('title', 'No title available'),
                    'thumbnail': info.get('thumbnail', ''),
                    'formats': available_formats
                }
    except Exception as e:
        print(f"Error fetching video info for {url}: {str(e)}")
        return None