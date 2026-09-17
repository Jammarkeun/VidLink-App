import os
import sys
import tempfile
import json
import re
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.pipeline import MediaExtractionPipeline
from backend.services.downloader import MediaDownloader
from backend.services.ffmpeg_utils import is_ffmpeg_available, get_ffmpeg_executable

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

pipeline = MediaExtractionPipeline()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "app": "VidLink Universal Media Extractor",
        "ffmpeg_available": is_ffmpeg_available(),
        "ffmpeg_path": get_ffmpeg_executable(),
        "extractors": [ext.name for ext in pipeline.extractors]
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_media():
    data = request.get_json(silent=True) or {}
    url = data.get('url')
    
    if not url:
        return jsonify({
            "success": False,
            "error_code": "MISSING_URL",
            "error": "URL parameter is required."
        }), 400

    result = pipeline.analyze_url(url)
    status_code = 200 if result.get('success') else (400 if result.get('error_code') == 'INVALID_URL' else 422)
    return jsonify(result), status_code

@app.route('/api/download', methods=['GET'])
def download_media():
    media_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    filename = re.sub(r'[^A-Za-z0-9._-]', '_', os.path.basename(filename)) or 'video.mp4'
    download_type = request.args.get('download_type', 'direct')
    format_id = request.args.get('format_id')
    source_url = request.args.get('source_url')
    video_url = request.args.get('video_url')
    audio_url = request.args.get('audio_url')
    headers = {}
    try:
        headers = json.loads(request.args.get('headers', '{}'))
        if not isinstance(headers, dict):
            headers = {}
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid download headers."}), 400

    if not media_url and not (video_url and audio_url):
        return jsonify({"error": "Missing download URL parameter."}), 400

    # Create temporary file for download output
    temp_dir = tempfile.mkdtemp(prefix="vidlink_")
    output_filepath = os.path.join(temp_dir, filename)

    try:
        success = False
        if download_type == 'ytdlp_format' and source_url and format_id:
            success = MediaDownloader.download_ytdlp(source_url, format_id, output_filepath)
        elif video_url and audio_url:
            # Merge separate video & audio streams using FFmpeg
            success = MediaDownloader.merge_video_audio(video_url, audio_url, output_filepath, headers=headers)
        elif download_type in ['hls', 'dash']:
            # Stream capture via FFmpeg
            success = MediaDownloader.download_ffmpeg_stream(media_url, output_filepath, headers=headers)
        else:
            # Direct HTTP file download
            success = MediaDownloader.download_direct(media_url, output_filepath, headers=headers)

        if not success and download_type not in ['hls', 'dash'] and not (video_url and audio_url):
            # Fallback to direct download if FFmpeg fails or is absent
            success = MediaDownloader.download_direct(media_url, output_filepath, headers=headers)

        if success and os.path.exists(output_filepath):
            return send_file(
                output_filepath,
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({
                "success": False,
                "error": "Media detected, but the resource cannot be downloaded through the available interface."
            }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Media extraction/download failed: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    print(f"Starting VidLink Universal Media Extraction Server on http://127.0.0.1:{port}...")
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG') == '1')
