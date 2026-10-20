"""
AI Adaptive Traffic Signal Digital Twin - Public Safety & Crime Scene Detection Engine
Utilizes simulated multi-sensor CCTV Optical Flow, Weapon Detection AI, and Acoustic Threat Analysis
to perform sub-second Public Safety Triage.
Crucially determines whether to dispatch an immediate Police 100/112 CAD Flying Squad
or suppress false alarms (such as everyday verbal disputes or street vendor tools) to protect police bandwidth.
"""

import time
from .config import SIM_CONFIG

class CrimeDetector:
    def __init__(self):
        self.active_crime = None
        self.crime_history = []
        self.police_config = SIM_CONFIG.get("CRIME_SYSTEM", {})
        self.counter = 1

    def trigger_crime(self, threat_type="CRITICAL", road_id="B"):
        """
        Triggers a crime / public safety event and executes sub-second AI threat triage.
        threat_type: 'CRITICAL' (Armed Assault / Knife Attack) or 'MINOR' (Verbal Dispute / False Alarm)
        """
        self.counter += 1
        incident_id = f"CAD-2026-POLICE-{2000 + self.counter}"
        timestamp = time.strftime("%H:%M:%S")

        if threat_type == "CRITICAL":
            weapon_detected = "Tactical Blade / Knife (94.2% AI Confidence)"
            harsh_behavior = "Severe Physical Assault & Weapon Aggression"
            acoustic_signature = "89.4 dB (Distress Scream & Violent Clamor)"
            threat_score = 95
            classification = "CRITICAL_ARMED_ASSAULT"
            call_police = True
            triage_reason = (
                f"CRITICAL VIOLENCE TRIAGE: High-threat weapon signature ({weapon_detected}) "
                f"and violent physical assault detected via Road {road_id} High-Res AI CCTV & Acoustic Arrays. "
                f"SYSTEM DECISION: AUTO-DISPATCH IMMEDIATE POLICE 100/112 CAD CALL WITH LIVE GPS & PCR INTERCEPTOR ALERT."
            )
            cad_status = "CONNECTING_POLICE_CONTROL_ROOM"
            traffic_action = "BLUE_RED_POLICE_STROBE_SURVEILLANCE_LOCK"
        else: # MINOR / FALSE ALARM SUPPRESSION
            weapon_detected = "None (Cooking / Street Vendor Tool Confirmed - 12% Hazard)"
            harsh_behavior = "Verbal Argument / Non-Violent Gesticulation"
            acoustic_signature = "64.2 dB (Elevated Ambient Speech)"
            threat_score = 15
            classification = "MINOR_VERBAL_DISPUTE"
            call_police = False
            triage_reason = (
                f"NON-CRITICAL / FALSE-ALARM SUPPRESSION: Zero weapon threat detected ({weapon_detected}). "
                f"Physical dispute classified as non-violent verbal disagreement. "
                f"SYSTEM DECISION: DO NOT CALL POLICE 100/112. Preserving police bandwidth & PCR Flying Squad units for genuine life-threatening crimes. "
                f"Telemetry logged to RSU edge storage with timestamp."
            )
            cad_status = "NO_CALL_DISPATCHED_SUPPRESSED"
            traffic_action = "LOCAL_SURVEILLANCE_LOG_ONLY"

        crime_data = {
            "incidentId": incident_id,
            "timestamp": timestamp,
            "roadId": road_id,
            "classification": classification,
            "threatScore": threat_score,
            "weaponDetected": weapon_detected,
            "harshBehavior": harsh_behavior,
            "acousticSignature": acoustic_signature,
            "callPolice": call_police,
            "triageReason": triage_reason,
            "cadStatus": cad_status,
            "cadTimer": 0.0,
            "trafficAction": traffic_action,
            "police": {
                "station": self.police_config.get("POLICE_STATION", "Central City Police Station & Cyber Traffic Control"),
                "phone": self.police_config.get("POLICE_PHONE", "112 / 100"),
                "dispatchCode": self.police_config.get("EMERGENCY_DISPATCH_CODE", "CAD-POLICE-112-METRO-PCR-4"),
                "gps": self.police_config.get("GPS_LOCATION", {}),
                "etaPcrMin": 2.4 if call_police else None
            },
            "audioTranscript": (
                f"Police 100/112 Auto-CAD: Armed Assault (Knife) at Central Junction (Main Arterial Corridor). "
                f"Threat Score: {threat_score}/100. PCR Flying Squad Dispatched."
            ) if call_police else "Notice: Non-violent verbal dispute. Police dispatch suppressed to protect emergency bandwidth."
        }

        self.active_crime = crime_data
        self.crime_history.insert(0, dict(crime_data))
        if len(self.crime_history) > 20:
            self.crime_history.pop()

        return crime_data

    def clear_crime(self):
        """Clears active crime state."""
        self.active_crime = None

    def update(self, dt):
        """Updates internal timers and CAD dispatch progression."""
        if not self.active_crime:
            return

        crm = self.active_crime
        if crm["callPolice"]:
            crm["cadTimer"] += dt
            if crm["cadStatus"] == "CONNECTING_POLICE_CONTROL_ROOM" and crm["cadTimer"] > 1.2:
                crm["cadStatus"] = "CAD_PACKET_TRANSMITTED_GPS_LOCKED"
            elif crm["cadStatus"] == "CAD_PACKET_TRANSMITTED_GPS_LOCKED" and crm["cadTimer"] > 3.0:
                crm["cadStatus"] = "PCR_FLYING_SQUAD_DISPATCHED_EN_ROUTE"

    def to_dict(self):
        return {
            "hasActiveCrime": self.active_crime is not None,
            "activeCrime": self.active_crime,
            "recentIncidents": self.crime_history[:5]
        }
