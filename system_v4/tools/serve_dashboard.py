#!/usr/bin/env python3
import http.server
import socketserver
import os
import webbrowser
import threading
import time

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    # Disable excessive logging
    def log_message(self, format, *args):
        pass

def open_browser():
    time.sleep(1)
    print(f"\n[Codex Ratchet Visualization Engine]")
    print(f"Launching Global Evidence Telemetry at: http://localhost:{PORT}/evidence_dashboard.html")
    print(f"Press Ctrl+C to stop the server.\n")
    webbrowser.open(f'http://localhost:{PORT}/evidence_dashboard.html')

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    threading.Thread(target=open_browser, daemon=True).start()
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Visualization Engine.")
