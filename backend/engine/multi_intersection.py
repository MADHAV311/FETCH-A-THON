"""
AI Adaptive Traffic Signal Digital Twin - Multi-Intersection Arterial Corridor
Coordinates surrounding traffic signals along the Metropolitan Arterial corridor.
Provides cooperative Green Wave synchronization, platoon arrival predictions,
and corridor-wide emergency vehicle preemption propagation.
"""

from .config import SIM_CONFIG

class MultiIntersectionCorridor:
    def __init__(self):
        corridor_cfg = SIM_CONFIG["MULTI_INTERSECTION"]
        self.corridor_name = corridor_cfg["CORRIDOR_NAME"]
        self.speed_limit_kmh = corridor_cfg["SPEED_LIMIT_KMH"]
        self.speed_limit_mps = self.speed_limit_kmh * (1000.0 / 3600.0) # ~12.5 m/s

        self.nodes = [
            {
                "id": "I-1",
                "name": "Upstream Feeder Junction",
                "role": "Upstream Feeder (West)",
                "distanceMeters": -650,
                "signalState": "GREEN",
                "phaseRemaining": 18.5,
                "cycleTime": 60.0,
                "inboundPlatoonVehicles": 12,
                "platoonEtaSec": 52.0, # distance / speed
                "greenWaveActive": True
            },
            {
                "id": "I-2",
                "name": "Central Junction (Digital Twin Main)",
                "role": "Hero Active Twin",
                "distanceMeters": 0,
                "signalState": "GREEN",
                "phaseRemaining": 15.0,
                "cycleTime": 50.0,
                "inboundPlatoonVehicles": 8,
                "platoonEtaSec": 0.0,
                "greenWaveActive": True
            },
            {
                "id": "I-3",
                "name": "Downstream Exit Junction",
                "role": "Downstream Exit (East)",
                "distanceMeters": 750,
                "signalState": "RED",
                "phaseRemaining": 8.0,
                "cycleTime": 60.0,
                "inboundPlatoonVehicles": 4,
                "platoonEtaSec": 60.0,
                "greenWaveActive": True
            }
        ]

        self.corridor_metrics = {
            "greenWaveCoherencePct": 88.5,
            "corridorStopsAvoided": 34,
            "corridorTravelTimeReductionSec": 42.0,
            "i2iLatencyMs": 8.4,
            "coordinationMode": "COOPERATIVE_GREEN_WAVE" # "COOPERATIVE_GREEN_WAVE", "EMERGENCY_CLEAR_CARPET", "ISOLATED"
        }

    def update(self, dt, hero_signal_state="GREEN", hero_phase_remaining=15.0, is_emergency_active=False, emergency_road="B"):
        """
        Updates surrounding signal states in lockstep with the hero digital twin.
        """
        # Node I-1 (Upstream) update
        n1 = self.nodes[0]
        n1["phaseRemaining"] -= dt
        if n1["phaseRemaining"] <= 0:
            if n1["signalState"] == "GREEN":
                n1["signalState"] = "YELLOW"
                n1["phaseRemaining"] = 3.5
            elif n1["signalState"] == "YELLOW":
                n1["signalState"] = "RED"
                n1["phaseRemaining"] = 28.0
            else:
                n1["signalState"] = "GREEN"
                n1["phaseRemaining"] = 28.5

        # Node I-2 (Hero Twin) directly syncs with simulated twin state
        n2 = self.nodes[1]
        n2["signalState"] = hero_signal_state
        n2["phaseRemaining"] = round(hero_phase_remaining, 1)

        # Node I-3 (Downstream) update
        n3 = self.nodes[2]
        if is_emergency_active and emergency_road in ("B", "D"): # East-West corridor
            # Emergency Corridor Preemption Wave! Downstream turns GREEN in advance
            n3["signalState"] = "GREEN"
            n3["phaseRemaining"] = 35.0
            self.corridor_metrics["coordinationMode"] = "EMERGENCY_CLEAR_CARPET"
            self.corridor_metrics["greenWaveCoherencePct"] = 100.0
        else:
            n3["phaseRemaining"] -= dt
            if n3["phaseRemaining"] <= 0:
                if n3["signalState"] == "GREEN":
                    n3["signalState"] = "YELLOW"
                    n3["phaseRemaining"] = 3.5
                elif n3["signalState"] == "YELLOW":
                    n3["signalState"] = "RED"
                    n3["phaseRemaining"] = 24.0
                else:
                    n3["signalState"] = "GREEN"
                    n3["phaseRemaining"] = 32.5
            self.corridor_metrics["coordinationMode"] = "COOPERATIVE_GREEN_WAVE"

    def to_dict(self):
        return {
            "corridorName": self.corridor_name,
            "speedLimitKmh": self.speed_limit_kmh,
            "metrics": self.corridor_metrics,
            "nodes": self.nodes
        }
