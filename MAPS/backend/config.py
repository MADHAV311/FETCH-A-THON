"""
TrafficFlow-MAPS: Signal-Aware Proactive Navigation & Multi-Agent Commuter Rerouting Copilot
Global Configuration, Geometries, Road Network, and MoRTH Economic Benchmarks.
"""

MAPS_CONFIG = {
    "PROJECT_NAME": "TrafficFlow-MAPS",
    "SUBTITLE": "Signal-Aware Proactive Navigation & Multi-Agent Commuter Rerouting Copilot",
    "VERSION": "1.0.0",
    "AUTHOR": "Team FETCHATHON3.0-8799 (BANDILA MADHAV et al.)",
    "PORT": 8085,

    # Geographic Context (Metropolitan Smart City Arterial Corridor)
    "ORIGIN": {
        "name": "Koramangala 4th Block (Start Point)",
        "lat": 12.9352,
        "lng": 77.6245,
        "x": 80,
        "y": 420
    },
    "DESTINATION": {
        "name": "Electronic City Phase 1 Tech Hub (Destination)",
        "lat": 12.8452,
        "lng": 77.6602,
        "x": 880,
        "y": 140
    },

    # Bottleneck Junction
    "CENTRAL_JUNCTION": {
        "name": "Central Arterial Junction (Signal-Controlled)",
        "lat": 12.9172,
        "lng": 77.6385,
        "x": 480,
        "y": 320,
        "default_queue_cars": 34,
        "red_phase_remaining_sec": 44.0,
        "signal_state": "RED",
        "active_incident": "108 Ambulance Green Carpet Preemption Active"
    },

    # Diversion Waypoint (The critical point where the user can turn right before being trapped)
    "DIVERSION_POINT": {
        "name": "8th Cross Ring Bypass Junction",
        "x": 320,
        "y": 380,
        "distance_to_bottleneck_meters": 350
    },

    # Route Specifications
    "ROUTES": {
        "DEFAULT_ROUTE": {
            "id": "ROUTE_DEFAULT",
            "name": "Direct Arterial (Through Central Junction)",
            "description": "Shortest distance on paper, but suffers severe 34-car bottleneck and red light wait",
            "distance_km": 4.2,
            "free_flow_eta_min": 7.5,
            "congested_eta_min": 15.2,
            "is_congested": True,
            "congestion_color": "#ef4444", # Red
            "waypoints": [
                {"x": 80, "y": 420, "label": "Start"},
                {"x": 220, "y": 400},
                {"x": 320, "y": 380, "label": "8th Cross Exit (Last Turn)"},
                {"x": 480, "y": 320, "label": "Central Junction (Red Signal)"},
                {"x": 680, "y": 230},
                {"x": 880, "y": 140, "label": "Destination"}
            ]
        },
        "PROACTIVE_BYPASS": {
            "id": "ROUTE_BYPASS",
            "name": "8th Cross Green Wave Bypass",
            "description": "Smooth diversion route synchronized with green wave corridor — skips the bottleneck completely",
            "distance_km": 4.8,
            "free_flow_eta_min": 8.1,
            "congested_eta_min": 8.6,
            "is_congested": False,
            "congestion_color": "#10b981", # Emerald Green
            "waypoints": [
                {"x": 80, "y": 420, "label": "Start"},
                {"x": 220, "y": 400},
                {"x": 320, "y": 380, "label": "Take Right Turn"},
                {"x": 420, "y": 520, "label": "Ring Bypass South"},
                {"x": 640, "y": 490},
                {"x": 760, "y": 340, "label": "Re-enter Arterial Corridor"},
                {"x": 880, "y": 140, "label": "Destination"}
            ]
        }
    },

    # Vehicle Kinematics
    "VEHICLE": {
        "max_speed_kmh": 45.0,
        "cruising_speed_px_sec": 70.0,
        "congested_speed_px_sec": 8.0,
        "acceleration": 40.0,
        "deceleration": 60.0
    },

    # MoRTH Indian Economic Factors
    "ECONOMICS": {
        "FUEL_PRICE_INR_PER_LITER": 102.50,
        "COMMUTER_TIME_VALUE_INR_PER_HOUR": 150.00,
        "IDLE_FUEL_LITERS_PER_HOUR": 1.2,
        "CO2_KG_PER_LITER": 2.31,
        "AVERAGE_COMMUTERS_PER_DAY": 18500
    },

    # Multi-Agent Swarm Configuration (Fetch.ai uAgents & Agentverse)
    "AGENTS": {
        "COMMUTER_AGENT": {
            "name": "commuter_navigation_agent",
            "port": 8011,
            "seed": "commuter_navigation_agent_seed_2026_metro_koramangala"
        },
        "JUNCTION_HUB_AGENT": {
            "name": "junction_signal_hub_agent",
            "port": 8012,
            "seed": "junction_signal_hub_agent_seed_2026_central"
        },
        "ALMANAC_AGENT": {
            "name": "almanac_gps_resolver_agent",
            "port": 8013,
            "seed": "almanac_gps_resolver_agent_seed_2026_metro"
        },
        "ASIONE_COPILOT_AGENT": {
            "name": "asione_navigation_copilot_agent",
            "port": 8010,
            "seed": "asione_navigation_copilot_agent_seed_2026_metro",
            "agentverse_handle": "@trafficflow-maps",
            "autonomous_address": "agent1qwmawnyywfmhxgtyfl6uut9gkv4s36q4ykw220trle6053c4k8nrzvp98t4"
        }
    }
}
