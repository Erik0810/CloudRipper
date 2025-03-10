import multiprocessing

# Gunicorn configuration for CloudRipper
bind = "0.0.0.0:10000"  # Use port 10000 as required by Render
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 300  # Increased timeout for long-running downloads
max_requests = 100
max_requests_jitter = 10
keepalive = 5
threads = 1

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
