from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from app.models import DownloadTask
from app import db
import os
import re
import uuid
import threading
import tempfile
import zipfile
import time
import traceback
import yt_dlp
import json
import requests
import logging
from urllib.parse import urlparse
from datetime import datetime
import subprocess

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Create blueprint
main_bp = Blueprint('main', __name__)

def check_dependencies():
    """Check if all required dependencies are installed"""
    # Check FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        logger.info("FFmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("FFmpeg is not installed - required for audio processing")
        return False

@main_bp.route('/')
def index():
    """Render the main page"""
    logger.info("Rendering index page")
    return render_template('index.html')

@main_bp.route('/process', methods=['POST'])
def process_playlist():
    """Process a SoundCloud playlist URL"""
    logger.info("Received playlist processing request")

    # Check dependencies first
    if not check_dependencies():
        error_msg = "FFmpeg is not installed. Please install FFmpeg to process audio files."
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

    data = request.json
    playlist_url = data.get('playlist_url')

    logger.info(f"Processing playlist URL: {playlist_url}")

    # Validate URL (basic validation)
    if not playlist_url or not is_valid_soundcloud_url(playlist_url):
        logger.warning(f"Invalid SoundCloud playlist URL: {playlist_url}")
        return jsonify({'error': 'Invalid SoundCloud playlist URL'}), 400

    # Create a new download task
    task = DownloadTask(
        playlist_url=playlist_url,
        status='pending'
    )
    db.session.add(task)
    db.session.commit()
    task_id = task.id  # Store task ID for the thread

    logger.info(f"Created download task with ID: {task_id}")

    def thread_wrapper():
        try:
            logger.info("Starting download thread with debug logging")
            # Test yt-dlp configuration
            test_opts = {
                'quiet': False,  # Enable output
                'no_warnings': False,  # Show warnings
                'extract_flat': True,
                'skip_download': True,
                'logger': logger,
                'verbose': True,
                'dump_json': True,
                'extractor_args': {'soundcloud': {'client_id': os.environ.get('SOUNDCLOUD_CLIENT_ID')}},
            }

            # Test SoundCloud connection
            logger.info("Testing SoundCloud connection...")
            with yt_dlp.YoutubeDL(test_opts) as ydl:
                try:
                    test_info = ydl.extract_info(playlist_url, download=False)
                    if test_info:
                        logger.info("Successfully connected to SoundCloud")
                        logger.info(f"Playlist info: {json.dumps(test_info, indent=2)}")
                    else:
                        raise Exception("Failed to get playlist info")
                except Exception as e:
                    logger.error(f"SoundCloud connection test failed: {str(e)}")
                    raise

            # Get the Flask app instance
            from app import create_app
            app = create_app()

            # If test passed, proceed with download
            with app.app_context():
                task = DownloadTask.query.get(task_id)
                if task:
                    task.status = 'processing'
                    db.session.commit()
                    logger.info(f"Starting download for task {task_id}")
                    download_playlist(task_id, playlist_url)
                else:
                    logger.error(f"Task {task_id} not found before starting download")

        except Exception as e:
            error_msg = f"Thread error: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())

            # Get the Flask app instance for error handling
            from app import create_app
            app = create_app()

            with app.app_context():
                task = DownloadTask.query.get(task_id)
                if task:
                    task.status = 'failed'
                    task.error_message = error_msg
                    db.session.commit()

    # Start the download process in a background thread with error handling
    download_thread = threading.Thread(target=thread_wrapper)
    download_thread.daemon = True
    download_thread.start()

    logger.info(f"Started download thread for task ID: {task_id}")

    return jsonify({
        'task_id': task_id,
        'status': 'pending'
    })

@main_bp.route('/status/<task_id>')
def get_status(task_id):
    """Get the status of a download task"""
    try:
        logger.info(f"Status check for task ID: {task_id}")
        task = DownloadTask.query.get_or_404(task_id)

        task_data = {
            'status': task.status,
            'error_message': task.error_message if hasattr(task, 'error_message') else None,
            'progress': task.progress if hasattr(task, 'progress') else None
        }

        logger.info(f"Returning task data: {task_data}")
        return jsonify(task_data)

    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        return jsonify({
            'status': 'failed',
            'error_message': str(e)
        }), 500

@main_bp.route('/download/<task_id>')
def download_file(task_id):
    """Download the zip file for a completed task"""
    logger.info(f"Download request for task ID: {task_id}")
    task = DownloadTask.query.get_or_404(task_id)

    if task.status != 'completed' or not task.file_path:
        logger.warning(f"Download not ready for task {task_id}. Status: {task.status}")
        return jsonify({'error': 'Download not ready or failed'}), 400

    if not os.path.exists(task.file_path):
        logger.error(f"Download file not found for task {task_id}: {task.file_path}")
        task.status = 'failed'
        task.error_message = 'Download file not found'
        db.session.commit()
        return jsonify({'error': 'Download file not found'}), 404

    logger.info(f"Sending file for task {task_id}: {task.file_path}")
    return send_file(task.file_path, as_attachment=True, download_name=f"soundcloud_playlist_{task_id}.zip")

def is_valid_soundcloud_url(url):
    """Validate if the URL is a SoundCloud playlist URL"""
    pattern = r'^https?://(?:www\.)?soundcloud\.com/[^/]+/sets/[^/]+'
    return bool(re.match(pattern, url))

def get_playlist_info(playlist_url):
    """Get information about the playlist using yt-dlp"""
    logger.info(f"Getting playlist info for URL: {playlist_url}")
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'skip_download': True,
        'logger': logger,
        'extractor_args': {'soundcloud': {'client_id': os.environ.get('SOUNDCLOUD_CLIENT_ID')}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Extracting SoundCloud playlist info...")
            info = ydl.extract_info(playlist_url, download=False)
            logger.info(f"Successfully extracted playlist info. Entries: {len(info.get('entries', []))}")

            # Log detailed playlist information
            entries = info.get('entries', [])
            logger.info(f"Playlist title: {info.get('title', 'Unknown')}")
            logger.info(f"Playlist description: {info.get('description', 'No description')}")
            logger.info("Tracks in playlist:")
            for i, entry in enumerate(entries, 1):
                logger.info(f"  {i}. {entry.get('title', 'Unknown')} by {entry.get('uploader', 'Unknown artist')}")

            return info
    except Exception as e:
        logger.error(f"Error getting playlist info: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def download_track(track_url, output_dir, track_index, total_tracks, task_id):
    """Download a single track from SoundCloud"""
    logger.info(f"Downloading track {track_index+1}/{total_tracks} from URL: {track_url}")

    ydl_opts = {
        'format': 'bestaudio/best',  # Select best audio quality
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'verbose': True,
        'logger': logger,
        'progress_hooks': [lambda d: logger.info(f"Download progress: {d.get('status', 'unknown')}")],
        'extractor_args': {'soundcloud': {'client_id': os.environ.get('SOUNDCLOUD_CLIENT_ID')}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Starting download for track {track_index+1}")
            info = ydl.extract_info(track_url)
            if info:
                logger.info(f"Successfully downloaded track: {info.get('title', 'Unknown title')}")
                return True
            else:
                logger.error(f"No info returned for track {track_index+1}")
                return False
    except Exception as e:
        logger.error(f"Error downloading track {track_index+1}: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def download_playlist(task_id, playlist_url):
    """Download all songs from a SoundCloud playlist"""
    logger.info(f"Starting download process for task {task_id}, URL: {playlist_url}")

    with current_app.app_context():
        task = DownloadTask.query.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found in database")
            return

        try:
            task.status = 'processing'
            db.session.commit()
            logger.info(f"Updated task {task_id} status to 'processing'")

            # Create temporary directory for downloads
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Created temporary directory: {temp_dir}")

            # Ensure upload folder exists
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)

            zip_filename = f"playlist_{task_id}.zip"
            zip_path = os.path.join(upload_folder, zip_filename)
            logger.info(f"Zip file will be saved to: {zip_path}")

            # Get playlist information
            logger.info("Fetching playlist information...")
            playlist_info = get_playlist_info(playlist_url)

            if not playlist_info:
                raise Exception("Failed to retrieve playlist information")

            if 'entries' not in playlist_info:
                raise Exception("Failed to retrieve playlist tracks")

            tracks = playlist_info.get('entries', [])
            total_tracks = len(tracks)

            logger.info(f"Found {total_tracks} tracks in playlist")

            if total_tracks == 0:
                raise Exception("No tracks found in the playlist")

            # Download each track in the playlist
            downloaded_tracks = 0
            for i, track in enumerate(tracks):
                track_url = track.get('url')
                if not track_url:
                    logger.warning(f"No URL found for track {i+1}, skipping")
                    continue

                # Try to download the track
                success = download_track(track_url, temp_dir, i, total_tracks, task_id)

                if success:
                    downloaded_tracks += 1
                    # Update progress based on successful downloads
                    progress_percent = int((downloaded_tracks / total_tracks) * 100)
                    task.status = f"processing:{progress_percent}"
                    db.session.commit()
                    logger.info(f"Progress: {progress_percent}% ({downloaded_tracks}/{total_tracks} tracks)")
                else:
                    logger.warning(f"Failed to download track {i+1}, continuing with next track")

                # Small delay to prevent rate limiting
                time.sleep(1)

            if downloaded_tracks == 0:
                raise Exception("Failed to download any tracks")

            # Create a zip file with all downloaded songs
            logger.info(f"Creating zip file at {zip_path}")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname)
                        logger.info(f"Added {arcname} to zip file")

            # Update task status
            task.status = 'completed'
            task.file_path = zip_path
            task.completed_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"Task {task_id} completed successfully")

        except Exception as e:
            error_msg = f"Error in download process: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            try:
                task.status = 'failed'
                task.error_message = error_msg
                db.session.commit()
            except Exception as db_error:
                logger.error(f"Failed to update task status: {str(db_error)}")

        finally:
            # Clean up temp directory
            try:
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temp directory: {str(cleanup_error)}")
