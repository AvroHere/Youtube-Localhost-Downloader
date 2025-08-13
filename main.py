import os
import subprocess
import webbrowser
import threading
from flask import Flask, render_template, request, jsonify, Response
from yt_dlp import YoutubeDL
from urllib.parse import urlparse, parse_qs
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# --- Configuration ---
PORT = 5001
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# --- Helper Functions ---

def is_playlist(url):
    """Check if URL is a YouTube playlist."""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return 'list' in query or 'playlist' in parsed.path

def get_metadata(url):
    """Extract video/playlist metadata without an API key."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'force_generic_extractor': True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info.get('_type') == 'playlist':
                return {
                    'type': 'playlist',
                    'title': info.get('title'),
                    'entries': [
                        {
                            'id': entry.get('id'),
                            'title': entry.get('title'),
                            'url': entry.get('url'),
                            'thumbnail': f"https://i.ytimg.com/vi/{entry.get('id')}/mqdefault.jpg", 
                            'duration': entry.get('duration')
                        } 
                        for entry in info.get('entries', [])
                        if entry.get('id')
                    ]
                }
            else:
                return {
                    'type': 'video',
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'thumbnail': f"https://i.ytimg.com/vi/{info.get('id')}/hqdefault.jpg",
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'view_count': info.get('view_count')
                }
    except Exception as e:
        return {'error': f"Failed to get metadata: {str(e)}"}

def download_media(url, media_type, playlist_indices=None):
    """
    Download video or audio using yt-dlp with optimized settings.
    Supports both single videos and playlists.
    """
    def generate():
        original_cwd = os.getcwd()
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
        os.chdir(DOWNLOAD_FOLDER)

        def _progress_hook(d):
            if d['status'] == 'downloading':
                progress_info = {
                    "type": "download",
                    "percentage": d.get('_percent_str', '0%').strip().replace('%', ''),
                    "downloaded_bytes": d.get('downloaded_bytes'),
                    "total_bytes": d.get('total_bytes') or d.get('total_bytes_estimate'),
                    "speed": d.get('_speed_str', 'N/A'),
                    "eta": d.get('_eta_str', 'N/A'),
                }
                yield f"data: {json.dumps(progress_info)}\n\n"
            
            elif d['status'] == 'finished':
                status_update = {
                    "type": "processing",
                    "message": "Finalizing download..." if media_type == 'video' else "Converting to MP3..."
                }
                yield f"data: {json.dumps(status_update)}\n\n"

        # Base options
        ydl_opts = {
            'no_warnings': True,
            'progress_hooks': [_progress_hook],
            'outtmpl': '%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': not is_playlist(url) if not playlist_indices else False,
        }

        # Video-specific options
        if media_type == 'video':
            ydl_opts.update({
                'format': 'bestvideo[height<=1080]+bestaudio',
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            })
        # Audio-specific options
        else:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '0',  # Best quality
                }],
                'extractaudio': True,
            })

        if playlist_indices:
            ydl_opts['playlist_items'] = playlist_indices

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            yield "data: COMPLETE\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"
        finally:
            os.chdir(original_cwd)
            
    return generate()

# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_metadata', methods=['POST'])
def handle_metadata():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    metadata = get_metadata(url)
    return jsonify(metadata)

@app.route('/download', methods=['GET'])
def handle_download():
    url = request.args.get('url')
    media_type = request.args.get('media_type')
    playlist_indices = request.args.get('playlist_indices')
    
    if not url or not media_type:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    return Response(
        download_media(url, media_type, playlist_indices),
        mimetype='text/event-stream'
    )

# --- Auto-open browser functionality ---
def open_browser():
    webbrowser.open_new(f"http://127.0.0.1:{PORT}")

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(port=PORT, debug=True)