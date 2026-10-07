"""
Kills the Flask process whose PID was written by start_flask.py.
Usage: python stop_flask.py
"""
import os
import sys
import signal

PID_FILE = "flask.pid"

if not os.path.exists(PID_FILE):
    print("No flask.pid found, nothing to stop.")
    sys.exit(0)

with open(PID_FILE) as f:
    pid = int(f.read().strip())

try:
    os.kill(pid, signal.SIGTERM)
    print(f"Sent SIGTERM to Flask process {pid}")
except PermissionError:
    print(f"Permission denied killing PID {pid}")
except ProcessLookupError:
    print(f"Process {pid} already gone")

os.remove(PID_FILE)
