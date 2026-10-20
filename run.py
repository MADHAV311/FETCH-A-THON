#!/usr/bin/env python3
"""
AI Adaptive Traffic Signal Digital Twin - Unified Launcher
Problem Statement 1: AI Traffic Management, 108 CAD Emergency Triage,
Directional Pole Sirens, VRU Crosswalk Scramble, & Arterial Green Wave Corridor.
"""

import sys
import os

# Ensure current directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    banner = """
======================================================================
  TRAFFICFLOW-AI : SMART CITY ADAPTIVE TRAFFIC SIGNAL DIGITAL TWIN
  Metropolitan Arterial Corridor & 108 Emergency CAD Triage Engine
======================================================================
  [1] Directional Pole Sirens: Acoustic & Visual Beacon Wave
  [2] AI Accident Triage: Sub-Second CAD Dispatch vs Minor Resolution
  [3] Pedestrian VRU Safety: Barnes Dance All-Pedestrian Scramble
  [4] Multi-Intersection: Metropolitan Cooperative Green Wave
  [5] Smart City Economics: Fuel, Carbon, & Rupee ROI Analytics
----------------------------------------------------------------------
  * Architecture: Decoupled Frontend (HTML5/Canvas) & Backend Service
  * Starting Server on: http://localhost:8080
======================================================================
"""
    print(banner)
    import server
    server.main()
