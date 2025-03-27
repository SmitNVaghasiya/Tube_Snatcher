from flask import Flask, request, jsonify, send_file
import os
from details_featcher import fetch_video_info
from video_downloader import download_video

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/fetch_details', methods=['POST'])
async def fetch_details():
    url = request.form.get('url')
    format_type = request.form.get('format', 'mp4')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    result = await fetch_video_info(url, format_type)
    if result is None:
        return jsonify({'error': 'Failed to fetch video details'}), 500
    return jsonify(result)

@app.route('/download', methods=['POST'])
def download():
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

if __name__ == '__main__':
    app.run(debug=True)