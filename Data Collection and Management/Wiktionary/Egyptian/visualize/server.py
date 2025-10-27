"""
Simple HTTP Server for Egyptian Lemma Network Visualizer

This script starts a local web server to view the network visualization.
The visualization will be available at http://localhost:8000
"""

import http.server
import socketserver
import webbrowser
import os
import shutil
from pathlib import Path

PORT = 8000

# Change to the visualize directory
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Copy JSON file if it doesn't exist in visualize directory
json_source = script_dir.parent / 'lemma_networks.json'
json_dest = script_dir / 'lemma_networks.json'

if json_source.exists() and not json_dest.exists():
    print(f"Copying lemma_networks.json to visualize directory...")
    shutil.copy2(json_source, json_dest)
    print(f"✓ JSON file copied")

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Redirect root to index.html
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()
    
    def end_headers(self):
        # Add CORS headers to allow loading JSON
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Content-Type', 'application/json' if self.path.endswith('.json') else self.guess_type(self.path))
        super().end_headers()

    def log_message(self, format, *args):
        # Custom log format
        if not self.path.endswith('.ico'):  # Suppress favicon errors
            print(f"[Server] {self.address_string()} - {format % args}")

def main():
    print("="*80)
    print("Egyptian Lemma Network Visualizer - Local Server")
    print("="*80)
    print(f"\nStarting server on port {PORT}...")
    print(f"Server directory: {script_dir}")
    print(f"\nOpen your browser and navigate to:")
    print(f"  → http://localhost:{PORT}")
    print(f"\nPress Ctrl+C to stop the server")
    print("="*80 + "\n")
    
    # Try to open browser automatically
    try:
        webbrowser.open(f'http://localhost:{PORT}')
        print("✓ Browser opened automatically\n")
    except:
        print("⚠ Could not open browser automatically. Please open manually.\n")
    
    # Start server
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n" + "="*80)
            print("Server stopped by user")
            print("="*80)

if __name__ == '__main__':
    main()
