# CloudRipper - SoundCloud Playlist Downloader

## Project Overview
CloudRipper is a web application that enables users to download entire SoundCloud playlists. The application provides a simple interface for users to input a SoundCloud playlist URL and receive a ZIP file containing all tracks from that playlist.

## Project Structure
```
CloudRipper/
├── app/
│   ├── __init__.py
│   ├── models.py         # Database models
│   ├── routes.py         # Application routes and core logic
│   ├── static/
│   │   ├── css/         # Stylesheets
│   │   ├── img/         # Images
│   │   └── js/          # JavaScript files
│   └── templates/        # HTML templates
├── docs/                 # Documentation
├── instance/            # Instance-specific files
├── gunicorn.conf.py     # Gunicorn configuration
├── render.yaml          # Render deployment configuration
├── requirements.txt     # Python dependencies
└── run.py              # Application entry point
```

## Core Components

### Database Model
- `DownloadTask`: Tracks the status of playlist downloads
  - Fields: id, playlist_url, status, created_at, completed_at, file_path, error_message
  - Status states: pending, processing, completed, failed

### Main Features
1. **Playlist Processing**
   - URL validation for SoundCloud playlists
   - Background task processing using threading
   - Progress tracking and status updates
   - Error handling and reporting

2. **Download Management**
   - Asynchronous download processing
   - ZIP file creation for playlist tracks
   - Temporary file management
   - Download status monitoring

3. **Dependencies**
   - Requires FFmpeg for audio processing
   - Uses yt-dlp for SoundCloud interaction
   - Supports SoundCloud Client ID configuration

### API Endpoints
- `GET /`: Main application interface
- `POST /process`: Initiates playlist download
- `GET /status/<task_id>`: Checks download status
- `GET /download/<task_id>`: Downloads completed playlist ZIP

## Technical Stack
- Backend: Flask (Python)
- Database: SQLAlchemy
- External Tools: FFmpeg, yt-dlp
- Frontend: HTML, CSS, JavaScript
- Deployment: Gunicorn, Render

Last updated: 2025-03-11