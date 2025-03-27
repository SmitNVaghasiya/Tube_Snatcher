from flask import Flask, request, jsonify, send_file, render_template
import os
from details_featcher import fetch_video_info
from video_downloader import download_video

# Tell Flask where to find templates and static files
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index2.html')  # Path is correct now

@app.route('/fetch_details', methods=['POST'])
def fetch_details():
    url = request.form.get('url')
    selected_format = request.form.get('format', 'mp4')  # Default to mp4

    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400

    info, available_formats = fetch_video_info(url, selected_format)
    
    if info is None:
        return jsonify({'error': 'Failed to fetch video info'}), 400

    return jsonify({
        'title': info.get('title', 'No title available'),
        'thumbnail': info.get('thumbnail', ''),
        'formats': available_formats
    })

@app.route('/download', methods=['POST'])

def download():
    url = request.form.get('url')
    format_id = request.form.get('format_id')
    # file_type = request.form.get("")
    if not url or not format_id:
        return jsonify({'error': 'URL and format_id parameters are required'}), 400

    directory = 'Flask_api/temp'  # Update temp directory path
    filename, error, title, thumbnail = download_video(url, format_id, directory) # This is not sending the file format but we are using it in the video_download file
    # filename, error, title, thumbnail = download_video(url, format_id, directory, file_type)
    
    if error:
        return jsonify({'error': error}), 400

    return jsonify({'filename': os.path.basename(filename), 'title': title, 'thumbnail': thumbnail})

@app.route('/download_file/<filename>')
def download_file(filename):
    directory = 'temp'  # Update temp directory path
    safe_filename = os.path.basename(filename)  # Prevent path traversal
    filepath = os.path.join(directory, safe_filename)
    
    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404

    return send_file(filepath, as_attachment=True, download_name=safe_filename)

# This code is for Only Local Server
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)

# This code is for render Deployment
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
