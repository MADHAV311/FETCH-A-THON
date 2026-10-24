"""
TrafficFlow-MAPS: Full-Stack Application Server & 30Hz Navigation Engine
Serves REST API endpoints, static Google Maps-style navigation frontend, and background kinematics thread.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
import time
import json
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# Ensure MAPS directory is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from backend.config import MAPS_CONFIG
from backend.engine.navigation_sim import NavigationSim
from backend.api.handlers import (
    handle_get_state,
    handle_reroute_accept,
    handle_reroute_reject,
    handle_control,
    handle_asione_chat
)

PORT = MAPS_CONFIG.get("PORT", 8085)
FRONTEND_DIR = os.path.join(CURRENT_DIR, "frontend")

nav_sim = NavigationSim()
state_lock = threading.Lock()
sim_running = True

def simulation_background_loop():
    last_time = time.perf_counter()
    target_dt = 1.0 / 30.0 # 30 updates per second

    while sim_running:
        start = time.perf_counter()
        raw_dt = start - last_time
        last_time = start

        with state_lock:
            nav_sim.update(raw_dt)

        elapsed = time.perf_counter() - start
        sleep_time = max(0.001, target_dt - elapsed)
        time.sleep(sleep_time)

class MapsHttpHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path

            if path == "/api/nav/state":
                with state_lock:
                    res = handle_get_state(nav_sim)
                self._send_response_dict(res)
                return

            # Default to static file serving
            super().do_GET()
        except Exception as e:
            self._send_error_response(500, str(e))

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path

            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            payload = json.loads(body.decode("utf-8")) if body else {}

            if path == "/api/nav/reroute/accept":
                with state_lock:
                    res = handle_reroute_accept(nav_sim)
                self._send_response_dict(res)
                return

            elif path == "/api/nav/reroute/reject":
                with state_lock:
                    res = handle_reroute_reject(nav_sim)
                self._send_response_dict(res)
                return

            elif path == "/api/nav/control":
                with state_lock:
                    res = handle_control(nav_sim, payload)
                self._send_response_dict(res)
                return

            elif path == "/api/nav/chat":
                with state_lock:
                    res = handle_asione_chat(nav_sim, payload)
                self._send_response_dict(res)
                return

            self._send_error_response(404, f"Endpoint not found: {path}")

        except Exception as e:
            self._send_error_response(500, str(e))

    def _send_response_dict(self, res):
        body_bytes = res["body"].encode("utf-8")
        self.send_response(res["status"])
        self.send_header("Content-Type", res["content_type"])
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)
        self.wfile.flush()

    def _send_error_response(self, code, message):
        body_bytes = json.dumps({"error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)
        self.wfile.flush()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        if len(args) > 0 and "/api/nav/state" in str(args[0]):
            return
        super().log_message(format, *args)

def main():
    print("=" * 70)
    print("  TRAFFICFLOW-MAPS : SIGNAL-AWARE PROACTIVE NAVIGATION COPILOT")
    print("  Built for FETCH-A-THON 3.0 & ASI:ONE AGENT CHALLENGE")
    print("=" * 70)
    print(f"  * Web Navigation Dashboard: http://localhost:{PORT}")
    print(f"  * Real-Time Telemetry API:  http://localhost:{PORT}/api/nav/state")
    print("=" * 70)

    # Start simulation loop in daemon thread
    sim_thread = threading.Thread(target=simulation_background_loop, daemon=True)
    sim_thread.start()

    server = ThreadingHTTPServer(("0.0.0.0", PORT), MapsHttpHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        global sim_running
        sim_running = False
        print("\nStopping TrafficFlow-MAPS Server...")
        server.server_close()

if __name__ == "__main__":
    main()
