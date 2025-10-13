import http.server
import socketserver
import json
import threading

# Shared status dictionary
status = {"status": "offline", "last_check": None}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='frontend', **kwargs)

    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode('utf-8'))
        elif self.path == '/recordings':
            try:
                with open('recording_log.jsonl', 'r') as f:
                    recordings = [json.loads(line) for line in f]
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(recordings).encode('utf-8'))
            except FileNotFoundError:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps([]).encode('utf-8'))
        else:
            super().do_GET()

def run_server():
    with socketserver.TCPServer(("", 8000), Handler) as httpd:
        print("Server started at localhost:8000")
        httpd.serve_forever()

def start_server_thread():
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    return server_thread
