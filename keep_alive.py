"""
Keep Alive Service for Render Free Plan
Creates a simple HTTP server to prevent Render from sleeping the service.
Also provides health check endpoint for monitoring.
"""

import threading
import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import logging

logger = logging.getLogger(__name__)

class KeepAliveHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for keep-alive pings and health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            response = """
            <!DOCTYPE html>
            <html>
            <head><title>Email Monitor - Keep Alive</title></head>
            <body>
                <h1>📧 Email Monitor Service</h1>
                <p>✅ Service is running and monitoring emails</p>
                <p>🔄 Keep-alive service active</p>
                <p>📊 <a href="/health">Health Check</a></p>
            </body>
            </html>
            """
            self.wfile.write(response.encode())
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = '{"status": "healthy", "service": "email_monitor", "keep_alive": "active"}'
            self.wfile.write(response.encode())
            
        elif self.path == '/ping':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'pong')
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_HEAD(self):
        """Handle HEAD requests for health checks"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        return

class KeepAliveService:
    """Keep alive service to prevent Render from sleeping"""
    
    def __init__(self, port=10000):
        self.port = port
        self.server = None
        self.running = False
        
        # Get service URL from environment (set by Render)
        self.service_url = os.getenv('RENDER_EXTERNAL_URL')
        if not self.service_url:
            # Fallback for local testing
            self.service_url = f'http://localhost:{port}'
    
    def start_server(self):
        """Start the HTTP server in a separate thread"""
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), KeepAliveHandler)
            self.running = True
            
            def run_server():
                logger.info(f"Keep-alive server starting on port {self.port}")
                self.server.serve_forever()
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            logger.info(f"✅ Keep-alive service started at {self.service_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start keep-alive server: {e}")
            return False
    
    def self_ping(self):
        """Send periodic pings to keep the service alive"""
        if not self.service_url:
            logger.warning("No service URL available for self-ping")
            return
        
        ping_url = f"{self.service_url}/ping"
        
        while self.running:
            try:
                # Sleep first to avoid immediate ping on startup
                time.sleep(840)  # 14 minutes (Render sleeps after 15 minutes)
                
                if not self.running:
                    break
                
                response = requests.get(ping_url, timeout=10)
                if response.status_code == 200:
                    logger.info("✅ Self-ping successful - service kept alive")
                else:
                    logger.warning(f"Self-ping returned status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Self-ping failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in self-ping: {e}")
    
    def start_self_ping(self):
        """Start self-ping in a separate thread"""
        if self.service_url:
            ping_thread = threading.Thread(target=self.self_ping, daemon=True)
            ping_thread.start()
            logger.info("🔄 Self-ping service started")
        else:
            logger.warning("Service URL not available - self-ping disabled")
    
    def stop(self):
        """Stop the keep-alive service"""
        self.running = False
        if self.server:
            self.server.shutdown()
            logger.info("Keep-alive service stopped")

# Global keep-alive service instance
keep_alive_service = None

def start_keep_alive(port=10000):
    """Start the keep-alive service"""
    global keep_alive_service
    
    try:
        keep_alive_service = KeepAliveService(port)
        
        if keep_alive_service.start_server():
            keep_alive_service.start_self_ping()
            return True
        else:
            return False
            
    except Exception as e:
        logger.error(f"Failed to start keep-alive service: {e}")
        return False

def stop_keep_alive():
    """Stop the keep-alive service"""
    global keep_alive_service
    
    if keep_alive_service:
        keep_alive_service.stop()
        keep_alive_service = None

if __name__ == "__main__":
    # For testing the keep-alive service standalone
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Starting Keep-Alive Service...")
    
    if start_keep_alive():
        print("✅ Keep-alive service started successfully")
        print("🌐 Visit http://localhost:10000 to test")
        print("📊 Health check: http://localhost:10000/health")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping keep-alive service...")
            stop_keep_alive()
            print("✅ Service stopped")
    else:
        print("❌ Failed to start keep-alive service")