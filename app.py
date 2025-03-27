from flask import Flask, request, jsonify, render_template, Response, stream_with_context
import os
import time
import json
from details_featcher import fetch_video_info
from video_downloader import download_video

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch_details', methods=['POST'])
def fetch_details():
    url = request.form.get('url')
    format_type = request.form.get('format', 'mp4')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # Log when fetching starts
    print(f"Fetching started for {url}")

    # Measure the start time before fetching details
    start_time = time.time()

    # Fetch the video/playlist info
    result = fetch_video_info(url, format_type)

    # Calculate the time taken after fetching details
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Details fetched for {url}. Time taken: {time_taken:.2f} seconds")

    def generate():
        if result is None:
            yield json.dumps({'error': 'Failed to fetch video details'}) + '\n'
            return

        if result['type'] == 'playlist':
            # Stream playlist data incrementally
            yield json.dumps({
                'type': 'playlist',
                'title': result['title'],
                'thumbnail': result['thumbnail'],
                'videos': []  # Initial empty list
            }) + '\n'

            # Stream each video's details as they are fetched
            for video in result['videos']:
                yield json.dumps({
                    'type': 'video_update',
                    'video': video
                }) + '\n'
        else:
            # Single video, send all at once
            yield json.dumps(result) + '\n'

    # Stream the response
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/download', methods=['POST'])
def download():
    try:
        url = request.form.get('url')
        format_id = request.form.get('format_id')
        desired_height = request.form.get('desired_height')
        format_type = request.form.get('format', 'mp4')
        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        directory = 'temp'
        if not os.path.exists(directory):
            os.makedirs(directory)

        if format_id:
            filename, error, title, thumbnail = download_video(url, format_id, directory, format_type)
        else:
            filename, error, title, thumbnail = download_video(url, desired_height, directory, format_type)

        if error:
            return jsonify({'error': error}), 500
        return jsonify({'message': f'Downloaded: {title}', 'filename': filename, 'thumbnail': thumbnail})
    except Exception as e:
        print(f"Error during download: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)