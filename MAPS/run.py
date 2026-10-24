#!/usr/bin/env python3
"""
TrafficFlow-MAPS Unified Launcher
Runs the Proactive Navigation Server and displays system architecture banner.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    banner = """
======================================================================
  TRAFFICFLOW-MAPS : SIGNAL-AWARE PROACTIVE NAVIGATION COPILOT
  Autonomous Multi-Agent Bottleneck Bypass & Vehicle-to-Infrastructure
======================================================================
  * Problem: Standard Google Maps only turns RED after you are stuck!
  * Solution: Preempts congestion 350m in advance via Fetch.ai uAgents.
  * Integration: Agentverse Almanac Registry & ASI:One ACP Copilot.
  * Web Dashboard: http://localhost:8085
======================================================================
"""
    print(banner)
    import server
    server.main()
