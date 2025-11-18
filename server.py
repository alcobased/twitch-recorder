import http.server
import socketserver
import json
import threading
import os
import time  # Import time for sleep in stop_server

# Shared status dictionary, to be populated by the main script
channels_status = {}
httpd = None  # Global reference to the server instance
server_thread = None  # Global reference to the server thread

# Custom server class to allow immediate socket reuse


class ReusableTCPServer(socketserver.TCPServer):
    # This line fixes the 'Address already in use' error
    allow_reuse_address = True


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='frontend', **kwargs)

    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(channels_status).encode('utf-8'))
        elif self.path == '/recordings':
            try:
                with open('recording_log.jsonl', 'r') as f:
                    # Reverse the list to show newest recordings first
                    recordings = [json.loads(line) for line in f]
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(recordings[::-1]).encode('utf-8'))
            except FileNotFoundError:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps([]).encode('utf-8'))
        elif self.path == '/config':
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(config).encode('utf-8'))
            except FileNotFoundError:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(
                    json.dumps({'error': 'config.json not found'}).encode(
                        'utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/config':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                new_config = json.loads(post_data.decode('utf-8'))
                with open('config.json', 'w') as f:
                    json.dump(new_config, f, indent=4)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                # Inform the user they need to restart the service
                self.wfile.write(json.dumps(
                    {'message': 'Config updated successfully. Restart service to apply.'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def run_server():
    """Runs the HTTP server in the background thread."""
    global httpd
    # Use the reusable server class
    httpd = ReusableTCPServer(("", 8000), Handler)
    print("Server started at localhost:8000")
    httpd.serve_forever()


def start_server_thread():
    """Starts the HTTP server in a separate daemon thread."""
    global server_thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    return server_thread


def stop_server():
    """Shuts down the HTTP server gracefully when called from the main thread."""
    global httpd
    if httpd:
        print("Shutting down HTTP server...")
        # shutdown() must be called from a different thread than the one running serve_forever()
        threading.Thread(target=httpd.shutdown).start()
        # Give a moment for the shutdown to complete
        time.sleep(0.5)
        print("HTTP server shut down.")
