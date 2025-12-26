from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # Read the bundled aggregated data
        # In Vercel, the file should be in the same directory or root
        # We assume it's at the project root, so we might need to adjust path
        file_path = os.path.join(os.path.dirname(__file__), '../aggregated_sales.json')
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            self.wfile.write(json.dumps(data).encode('utf-8'))
        except Exception as e:
            error_msg = {"error": f"Failed to read data: {str(e)}", "path": file_path}
            self.wfile.write(json.dumps(error_msg).encode('utf-8'))
