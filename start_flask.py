"""
Starts the Flask app as a background process and waits until it is ready.
Writes the process PID to flask.pid so stop_flask.py can kill it cleanly.
Usage: python start_flask.py
"""
import subprocess
import sys
import time
import urllib.request
import os

FLASK_URL = "http://localhost:5000"
PID_FILE  = "flask.pid"
MAX_WAIT  = 30  # seconds

# Launch Flask using the same Python interpreter running this script
proc = subprocess.Popen(
    [sys.executable, "app.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Write PID so stop_flask.py can kill it
with open(PID_FILE, "w") as f:
    f.write(str(proc.pid))

print(f"Flask started with PID {proc.pid}, waiting for it to be ready...")

for i in range(MAX_WAIT):
    try:
        urllib.request.urlopen(FLASK_URL, timeout=2)
        print(f"Flask is up after {i+1}s")
        sys.exit(0)
    except Exception:
        time.sleep(1)

print(f"Flask did not start within {MAX_WAIT}s")
proc.kill()
sys.exit(1)
