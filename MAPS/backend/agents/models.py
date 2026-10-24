"""
TrafficFlow-MAPS: Typed Agent-to-Agent (A2A) Message Models (Fetch.ai uAgents Protocol)
"""

from uagents import Model
from typing import List, Optional, Dict, Any

class RouteCongestionQuery(Model):
    driver_id: str = "COMMUTER-KA-01-MJ-8821"
    current_lat: float = 12.9250
    current_lng: float = 77.6300
    destination_name: str = "Electronic City Phase 1 Tech Hub"
    planned_route_id: str = "DEFAULT_ROUTE"
    speed_kmh: float = 42.0

class ProactiveRerouteNotice(Model):
    bottleneck_detected: bool = True
    alert_level: str = "CRITICAL_BOTTLENECK" # "CRITICAL_BOTTLENECK" | "MODERATE_SLOWDOWN"
    junction_name: str = "Central Arterial Junction"
    current_queue_cars: int = 34
    red_phase_remaining_sec: float = 44.0
    is_emergency_preemption: bool = True
    bypass_road_name: str = "8th Cross Green Wave Bypass"
    turn_action_instruction: str = "Take Right Turn at 8th Cross (150m ahead)"
    time_saved_minutes: float = 6.2
    fuel_saved_liters: float = 0.42
    rupees_saved_inr: float = 45.80
    rationale: str

class RerouteActionCommand(Model):
    driver_id: str = "COMMUTER-KA-01-MJ-8821"
    decision: str = "ACCEPTED" # "ACCEPTED" | "REJECTED"
    chosen_route_id: str = "PROACTIVE_BYPASS"
    timestamp: float

class AlmanacLookupRequest(Model):
    query_lat: float = 12.9172
    query_lng: float = 77.6385
    service_type: str = "SMART_JUNCTION_ORCHESTRATION"

class AlmanacLookupResponse(Model):
    matched_agent_name: str = "junction_signal_hub_agent"
    matched_agent_address: str = "agent1q2z8k6x0w3h8f8j9s7l2m4n5p6q7r8s9t0u1v2w3x4y5z"
    distance_meters: float = 340.0
    status: str = "ONLINE_ACTIVE"

class NavigationTelemetry(Model):
    vehicle_x: float
    vehicle_y: float
    speed_kmh: float
    distance_traveled_km: float
    active_route: str
    reroute_status: str
    fuel_consumed_liters: float
