#!/usr/bin/env python3
"""
프론트엔드 개발 서버
"""
import http.server
import socketserver
import os
from pathlib import Path

PORT = 3000
FRONTEND_DIR = Path(__file__).parent

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

    def do_GET(self):
        """GET 요청 로깅"""
        print(f"\n📥 [GET 요청]")
        print(f"   - Path: {self.path}")
        print(f"   - Client: {self.client_address[0]}:{self.client_address[1]}")
        super().do_GET()

    def do_POST(self):
        """POST 요청 로깅"""
        print(f"\n📤 [POST 요청]")
        print(f"   - Path: {self.path}")
        print(f"   - Client: {self.client_address[0]}:{self.client_address[1]}")
        print(f"   - Content-Length: {self.headers.get('Content-Length', 'N/A')}")
        super().do_POST()

    def end_headers(self):
        # CORS 헤더 추가
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    os.chdir(FRONTEND_DIR)
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🌐 Frontend server running at http://localhost:{PORT}")
        print(f"📁 Serving files from: {FRONTEND_DIR}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ Server stopped")
