"""
AI Adaptive Traffic Signal Digital Twin - Accident Detection & Severity Triage Engine
Utilizes simulated multi-sensor telemetry (CCTV Optical Flow, Impact Deceleration G-force,
Acoustic Signature) to assess collision severity.
Critically performs sub-second AI triage to decide whether to dispatch an emergency
hospital CAD call or handle as a minor non-emergency fender-bender without clogging 108.
"""

import time
import math
from .config import SIM_CONFIG

class AccidentDetector:
    def __init__(self):
        self.active_accident = None
        self.accident_history = []
        self.hospital_config = SIM_CONFIG["ACCIDENT_SYSTEM"]
        self.counter = 1

    def trigger_accident(self, severity_type="CRITICAL", road_id="C", speed=None, g_force=None):
        """
        Triggers an accident event and executes sub-second AI severity triage.
        severity_type: 'CRITICAL' or 'MINOR'
        """
        self.counter += 1
        incident_id = f"CAD-2026-MED-{1000 + self.counter}"
        timestamp = time.strftime("%H:%M:%S")

        if severity_type == "CRITICAL":
            impact_speed = speed if speed is not None else 54.5 # km/h
            impact_g = g_force if g_force is not None else 6.8   # G-force
            airbags = True
            structural_intrusion = "Severe (Cabin Intrusion 32cm)"
            vehicles_involved = 2
            estimated_casualties = 2
            severity_score = 92 # out of 100
            classification = "CRITICAL_EMERGENCY"
            call_emergency = True
            triage_reason = (
                f"CRITICAL TRAUMA TRIAGE: High impact speed ({impact_speed:.1f} km/h) and severe {impact_g:.1f}G "
                f"impact spike detected via Road {road_id} CCTV & acoustic sensors. Airbag deployment confirmed. "
                f"SYSTEM DECISION: AUTO-DISPATCH IMMEDIATE 108 CAD EMERGENCY CALL TO TRAUMA CENTER WITH GPS COORDINATES."
            )
            cad_status = "CONNECTING_HOSPITAL"
            traffic_action = "PERIMETER_LOCKDOWN_UPSTREAM_RED_DOWNSTREAM_GREEN"
        else: # MINOR
            impact_speed = speed if speed is not None else 14.2 # km/h
            impact_g = g_force if g_force is not None else 1.3   # G-force
            airbags = False
            structural_intrusion = "Negligible (Surface Bumper Scrape)"
            vehicles_involved = 2
            estimated_casualties = 0
            severity_score = 18 # out of 100
            classification = "MINOR_FENDER_BENDER"
            call_emergency = False
            triage_reason = (
                f"NON-EMERGENCY TRIAGE: Low impact speed ({impact_speed:.1f} km/h) and minimal {impact_g:.1f}G force. "
                f"Airbags intact, zero structural cabin intrusion, zero casualties. "
                f"SYSTEM DECISION: DO NOT CALL 108 / HOSPITAL. Preserving ambulance bandwidth for genuine life-threatening emergencies. "
                f"Generating digital insurance log and activating advisory lane flush."
            )
            cad_status = "NO_CALL_DISPATCHED_RESOLVED_LOCALLY"
            traffic_action = "ADVISORY_LANE_FLUSH"

        accident_data = {
            "incidentId": incident_id,
            "timestamp": timestamp,
            "roadId": road_id,
            "classification": classification,
            "severityScore": severity_score,
            "impactSpeedKmh": impact_speed,
            "gForce": impact_g,
            "airbagsDeployed": airbags,
            "structuralIntrusion": structural_intrusion,
            "vehiclesInvolved": vehicles_involved,
            "estimatedCasualties": estimated_casualties,
            "callEmergency": call_emergency,
            "triageReason": triage_reason,
            "cadStatus": cad_status,
            "cadTimer": 0.0,
            "trafficAction": traffic_action,
            "hospital": {
                "name": self.hospital_config["HOSPITAL_NAME"],
                "phone": self.hospital_config["HOSPITAL_PHONE"],
                "dispatchCode": self.hospital_config["EMERGENCY_DISPATCH_CODE"],
                "gps": self.hospital_config["GPS_LOCATION"],
                "etaAmbulanceMin": 3.8 if call_emergency else None
            },
            "audioTranscript": (
                f"Emergency 108 Auto-CAD: Collision at Central Junction (Main Arterial Corridor). "
                f"Impact: {impact_g:.1f}G, Casualties: {estimated_casualties}. ALS Ambulance Dispatched."
            ) if call_emergency else "Notice: Minor non-injury fender bender. Digital incident record filed."
        }

        self.active_accident = accident_data
        self.accident_history.insert(0, dict(accident_data))
        if len(self.accident_history) > 20:
            self.accident_history.pop()

        return accident_data

    def clear_accident(self):
        """Clears the active accident state."""
        self.active_accident = None

    def update(self, dt):
        """Updates internal timers and CAD dispatch progression."""
        if not self.active_accident:
            return

        acc = self.active_accident
        if acc["callEmergency"]:
            acc["cadTimer"] += dt
            if acc["cadStatus"] == "CONNECTING_HOSPITAL" and acc["cadTimer"] > 1.2:
                acc["cadStatus"] = "CAD_PACKET_TRANSMITTED_GPS_LOCKED"
            elif acc["cadStatus"] == "CAD_PACKET_TRANSMITTED_GPS_LOCKED" and acc["cadTimer"] > 3.0:
                acc["cadStatus"] = "AMBULANCE_DISPATCHED_EN_ROUTE"

    def to_dict(self):
        return {
            "hasActiveAccident": self.active_accident is not None,
            "activeAccident": self.active_accident,
            "recentIncidents": self.accident_history[:5]
        }
