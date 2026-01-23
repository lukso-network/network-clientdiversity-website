#!/usr/bin/env python3
"""Simple HTTP server that serves static files and dynamic data from DATA_PATH."""

import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PORT = int(os.environ.get('PORT', 4000))
DATA_PATH = os.environ.get('DATA_PATH', '/data')
STATIC_DIR = os.environ.get('STATIC_DIR', '/app/_site')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        # Serve data files from DATA_PATH
        if self.path.startswith('/data/'):
            self.serve_data_file()
        else:
            super().do_GET()

    def serve_data_file(self):
        # Strip /data/ prefix and get file from DATA_PATH
        filename = self.path[6:]  # Remove '/data/'
        filepath = Path(DATA_PATH) / filename

        if not filepath.exists():
            self.send_error(404, f'File not found: {filename}')
            return

        try:
            content = filepath.read_bytes()
            self.send_response(200)

            # Set content type
            if filename.endswith('.json'):
                self.send_header('Content-Type', 'application/json')
            else:
                self.send_header('Content-Type', 'application/octet-stream')

            self.send_header('Content-Length', len(content))
            self.send_header('Cache-Control', 'no-cache, must-revalidate')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))


if __name__ == '__main__':
    print(f'Starting server on port {PORT}')
    print(f'Serving static files from: {STATIC_DIR}')
    print(f'Serving data files from: {DATA_PATH}')
    httpd = HTTPServer(('0.0.0.0', PORT), Handler)
    httpd.serve_forever()
