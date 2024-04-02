import http.server
import socketserver

class RedirectHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(301)  # 301 indicates a permanent redirect
        self.send_header('Location', 'https://freedium.cfd')
        self.end_headers()

port = 80
server = socketserver.TCPServer(('', port), RedirectHandler)
print(f"Redirect server running at http://localhost:{port}")
server.serve_forever()
