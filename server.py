import http.server
import socketserver
import json
import threading

# Shared status dictionary
status = {"status": "offline", "last_check": None}

class StatusHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    with socketserver.TCPServer(("", 8000), StatusHandler) as httpd:
        print("Server started at localhost:8000")
        httpd.serve_forever()

def start_server_thread():
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    return server_thread
