"""
TrafficFlow-MAPS: Signal-Aware Proactive Route Optimizer
Detects bottlenecks at downstream junctions in advance and calculates dynamic reroute advisories.
"""

from ..config import MAPS_CONFIG
from .indian_economics import IndianEconomicsCalculator

class RouteOptimizer:
    def __init__(self):
        self.config = MAPS_CONFIG
        self.economics = IndianEconomicsCalculator()
        self.default_route = self.config["ROUTES"]["DEFAULT_ROUTE"]
        self.bypass_route = self.config["ROUTES"]["PROACTIVE_BYPASS"]
        self.junction = self.config["CENTRAL_JUNCTION"]

    def evaluate_traffic_hurdle(self, current_queue: int = 34, red_remaining: float = 44.0, is_emergency: bool = True):
        """
        Calculates whether the upcoming junction qualifies as a severe bottleneck
        and generates a proactive bypass recommendation.
        """
        # Estimated clearance time per queued vehicle ~ 1.8s (saturation headway) + startup lost time (2.5s)
        queue_clearance_sec = (current_queue * 1.8) + 2.5
        total_bottleneck_delay_sec = red_remaining + queue_clearance_sec
        total_bottleneck_delay_min = total_bottleneck_delay_sec / 60.0

        default_eta_min = round(self.default_route["free_flow_eta_min"] + total_bottleneck_delay_min, 1)
        bypass_eta_min = round(self.bypass_route["congested_eta_min"], 1)

        time_saved_min = max(0.0, round(default_eta_min - bypass_eta_min, 1))
        idle_saved_sec = max(0.0, round(total_bottleneck_delay_sec, 1))

        # Financial & Carbon metrics
        savings = self.economics.calculate_reroute_savings(time_saved_min, idle_saved_sec)

        should_reroute = time_saved_min >= 2.0 or current_queue >= 15 or is_emergency

        alert_level = "CRITICAL_BOTTLENECK" if (current_queue >= 25 or is_emergency) else "MODERATE_SLOWDOWN"
        reason_text = (
            f"Central Junction has {current_queue} queued vehicles with {red_remaining:.0f}s RED phase remaining. "
            f"{'108 Ambulance Green Carpet Preemption Active.' if is_emergency else ''} "
            f"Bypass via 8th Cross avoids this queue completely."
        )

        return {
            "shouldReroute": should_reroute,
            "alertLevel": alert_level,
            "junctionName": self.junction["name"],
            "currentQueueCars": current_queue,
            "redPhaseRemainingSec": red_remaining,
            "isEmergencyActive": is_emergency,
            "reason": reason_text,
            "defaultRoute": {
                "name": self.default_route["name"],
                "distanceKm": self.default_route["distance_km"],
                "etaMinutes": default_eta_min,
                "status": "CONGESTED_RED"
            },
            "recommendedBypass": {
                "name": self.bypass_route["name"],
                "action": "Turn Right at 8th Cross (150m ahead)",
                "distanceKm": self.bypass_route["distance_km"],
                "etaMinutes": bypass_eta_min,
                "status": "CLEAR_GREEN_WAVE"
            },
            "savings": savings
        }
