Project Name: Cloudripper

Description:
Cloudripper is a modern, minimalist website inspired by the aesthetics of Serial Experiments Lain. It allows users to input a SoundCloud playlist link and download all songs from the playlist in a zip file.

Core Features:

User-friendly interface with a cyberpunk, retro-tech aesthetic.

Input field to paste a SoundCloud playlist URL.

Backend service to fetch and download all songs from the playlist.

Zipping functionality to bundle all songs into a single downloadable file.

API integration with SoundCloud for playlist parsing.

Queue system for handling multiple download requests.

Responsive design with a focus on dark-themed UI.

Log system for tracking download requests.

Technical Stack:

Backend: Flask (Python)

Frontend: HTML, CSS (Tailwind or Bootstrap), JavaScript (Alpine.js or React for interactivity)

Database: SQLite or PostgreSQL for storing request logs

Storage: Temporary storage (e.g., local filesystem or cloud-based solution like S3) for handling zipped files

API Handling: SoundCloud API, youtube-dl/yt-dlp (for fetching songs)

Task Queue: Celery + Redis (for handling asynchronous downloads)

Endpoints:

Home (/) : Landing page with input field and instructions.

Process (/process) : Accepts a playlist URL, validates it, and queues a download job.

Download (/download/<task_id>) : Allows users to download the generated zip file.

Status (/status/<task_id>) : Returns the progress of an ongoing download.

UI Design Considerations:

Minimalist interface with glitch effects and cyberpunk elements.

Monospaced fonts, terminal-like aesthetics, and animated elements.

Background effects reminiscent of Serial Experiments Lain (glowing text, distorted grids, dark UI with neon highlights).

Progress bar or terminal-style log updates for download status.