"""
TrafficFlow-MAPS Automated Verification Test Suite
Tests navigation kinematics, route optimization, MoRTH economics,
Fetch.ai typed A2A schemas, and ASI:One ACP v0.3.0 intent-to-action engine
including Location-Specific Traffic Intelligence queries.
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

from backend.config import MAPS_CONFIG
from backend.engine.indian_economics import IndianEconomicsCalculator
from backend.engine.route_optimizer import RouteOptimizer
from backend.engine.navigation_sim import NavigationSim
from backend.agents.models import (
    RouteCongestionQuery,
    ProactiveRerouteNotice,
    RerouteActionCommand,
    AlmanacLookupRequest,
    AlmanacLookupResponse
)
from backend.agents.agent_asione_copilot import process_copilot_intent

def run_tests():
    print("=" * 70)
    print("  TRAFFICFLOW-MAPS : AUTOMATED VERIFICATION TEST SUITE")
    print("=" * 70)

    # TEST 1: MoRTH Economics Calculator
    print("\n[TEST 1] Verifying MoRTH Indian Economic ROI Formulations")
    eco = IndianEconomicsCalculator()
    res = eco.calculate_reroute_savings(delay_saved_minutes=6.2, idle_saved_seconds=372.0)
    assert res["delaySavedMinutes"] == 6.2, "Delay saved mismatch"
    assert res["fuelSavedLiters"] > 0.1, "Fuel saved should be positive"
    assert res["totalTripSavingsInr"] > 25.0, "Total trip savings should be > ₹25"
    assert res["annualizedCorridor"]["annualSavingsLakhs"] > 100.0, "Annual savings should exceed ₹100 Lakhs"
    print(f"  --> PASS: 6.2 min delay saved yields ₹{res['totalTripSavingsInr']} trip savings & ₹{res['annualizedCorridor']['annualSavingsLakhs']} Lakhs/yr corridor ROI!")

    # TEST 2: Route Optimizer & Traffic Hurdle Evaluation
    print("\n[TEST 2] Verifying Signal-Aware Route Optimizer Bottleneck Detection")
    opt = RouteOptimizer()
    hurdle = opt.evaluate_traffic_hurdle(current_queue=34, red_remaining=44.0, is_emergency=True)
    assert hurdle["shouldReroute"] is True, "Expected proactive reroute to be recommended"
    assert hurdle["alertLevel"] == "CRITICAL_BOTTLENECK", "Expected CRITICAL_BOTTLENECK"
    assert hurdle["recommendedBypass"]["etaMinutes"] < hurdle["defaultRoute"]["etaMinutes"], "Bypass must be faster than bottleneck"
    print(f"  --> PASS: 34-car bottleneck triggers proactive bypass recommendation (Bypass: {hurdle['recommendedBypass']['etaMinutes']}m vs Default: {hurdle['defaultRoute']['etaMinutes']}m)!")

    # TEST 3: Navigation Kinematics & Diversion Proximity Trigger
    print("\n[TEST 3] Verifying Navigation Kinematics & Diversion Proximity Trigger")
    sim = NavigationSim()
    assert sim.veh_x == 80.0 and sim.veh_y == 420.0, "Start coordinates mismatch"
    assert sim.reroute_decision == "PENDING", "Initial decision must be PENDING"
    assert sim.active_route_id == "DEFAULT_ROUTE", "Default route must be active initially"

    triggered = False
    for step in range(120):
        sim.update(0.1)
        if sim.alert_triggered:
            triggered = True
            break

    assert triggered is True, "Proactive alert banner should trigger within 350m of diversion"
    print(f"  --> PASS: Proactive alert banner successfully triggered at vehicle position ({sim.veh_x:.1f}, {sim.veh_y:.1f})!")

    # TEST 4: Accepting Reroute Transitions Trajectory
    print("\n[TEST 4] Verifying Dynamic Reroute Acceptance Transitions Path to Bypass")
    accept_res = sim.accept_reroute()
    assert accept_res["success"] is True, "Accept reroute failed"
    assert sim.active_route_id == "PROACTIVE_BYPASS", "Active route should now be PROACTIVE_BYPASS"
    assert sim.reroute_decision == "ACCEPTED", "Reroute decision should be ACCEPTED"
    print(f"  --> PASS: Reroute accepted! Vehicle dynamically switched to 8th Cross Green Wave Bypass.")

    # TEST 5: Fetch.ai Typed A2A Pydantic Schemas
    print("\n[TEST 5] Verifying Fetch.ai Typed Agent-to-Agent (A2A) Protocols")
    q = RouteCongestionQuery(driver_id="COMMUTER-01", current_lat=12.9250, current_lng=77.6300)
    notice = ProactiveRerouteNotice(
        bottleneck_detected=True,
        alert_level="CRITICAL_BOTTLENECK",
        junction_name="Central Arterial Junction",
        current_queue_cars=34,
        red_phase_remaining_sec=44.0,
        is_emergency_preemption=True,
        bypass_road_name="8th Cross Green Wave Bypass",
        turn_action_instruction="Turn Right in 150m",
        time_saved_minutes=6.2,
        fuel_saved_liters=0.42,
        rupees_saved_inr=45.80,
        rationale="Clear bypass"
    )
    cmd = RerouteActionCommand(driver_id="COMMUTER-01", decision="ACCEPTED", chosen_route_id="PROACTIVE_BYPASS", timestamp=100.0)
    almanac_req = AlmanacLookupRequest(query_lat=12.9172, query_lng=77.6385)
    almanac_res = AlmanacLookupResponse(matched_agent_name="junction_signal_hub_agent", matched_agent_address="agent1q...", distance_meters=340.0)
    print("  --> PASS: All 5 Fetch.ai uagents.Model schemas validated successfully!")

    # TEST 6: ASI:One Location-Specific Traffic Intelligence Queries
    print("\n[TEST 6] Verifying ASI:One Location-Specific Traffic Intelligence Queries")

    # 6.1 Congested Place: Silk Board
    reply_silk = process_copilot_intent("Is there traffic at Silk Board?")
    assert "YES, SEVERE TRAFFIC" in reply_silk or "HIGH BOTTLENECK" in reply_silk, "Silk Board should report traffic"
    assert "EXACT BOTTLENECK PINPOINT" in reply_silk, "Should include exact bottleneck pinpoint section"
    assert "Central Silk Board Bus Terminus" in reply_silk, "Should pinpoint exact epicenter landmark"
    assert "650 meters" in reply_silk, "Should report exact 650m backlog stretch"
    assert "48 vehicles" in reply_silk, "Should report 48 vehicles in queue"
    assert "Madiwala Underpass" in reply_silk, "Should give bypass recommendation"
    assert "agent1q9silkboard" in reply_silk, "Should return connected Fetch.ai agent address"
    print("  --> PASS: Silk Board query returns verdict + EXACT PINPOINT (Bus Terminus & 650m Backlog) + Fetch.ai Agent ID!")

    # 6.2 Free-flowing Place: Koramangala
    reply_kora = process_copilot_intent("Is Koramangala 4th Block clear?")
    assert "NO TRAFFIC" in reply_kora or "CLEAR & FREE-FLOWING" in reply_kora, "Koramangala should report clear"
    assert "ZERO BOTTLENECK DETECTED" in reply_kora, "Should report zero bottleneck"
    assert "0 meters" in reply_kora, "Should report 0 meters backlog stretch"
    assert "42.5 km/h" in reply_kora, "Should report speed"
    print("  --> PASS: Koramangala query returns verdict (NO TRAFFIC - CLEAR) + Zero Bottleneck verification!")

    # 6.3 Severe Junction with Ambulance: Central Junction
    reply_cj = process_copilot_intent("What is the traffic situation at Central Junction?")
    assert "YES, SEVERE TRAFFIC" in reply_cj, "Central Junction should report traffic"
    assert "EXACT BOTTLENECK PINPOINT" in reply_cj, "Should include exact bottleneck pinpoint section"
    assert "Metro Pillar #412" in reply_cj, "Should identify exact stopline landmark opposite Metro Pillar #412"
    assert "350 meters" in reply_cj, "Should identify exact 350m backlog stretch to 8th Cross"
    assert "Lanes 1 & 2" in reply_cj, "Should identify exact affected lanes"
    assert "108 ALS Ambulance" in reply_cj, "Should report 108 ambulance preemption"
    assert "8th Cross" in reply_cj, "Should recommend 8th Cross bypass"
    print("  --> PASS: Central Junction query pinpoints EXACT EPICENTER (Pillar #412, 350m stretch, Lanes 1 & 2 blocked)!")

    # 6.4 Custom / Arbitrary Place Query
    reply_custom = process_copilot_intent("How is traffic around Bannerghatta Road?")
    assert "Bannerghatta Road" in reply_custom, "Should identify custom location name"
    assert "MODERATE CONGESTION" in reply_custom, "Should report traffic estimate"
    assert "EXACT BOTTLENECK PINPOINT" in reply_custom, "Should include exact bottleneck pinpoint for custom query"
    assert "380 meters" in reply_custom, "Should calculate upstream backlog stretch"
    assert "agent1qbannerghattaroad" in reply_custom, "Should generate registered Fetch.ai agent address"
    print("  --> PASS: Custom location query dynamically generates EXACT BOTTLENECK LOCATION + MoRTH metrics!")

    # 6.5 Interactive Action: Natural Language Reroute Command
    sim_test = NavigationSim()
    reply_reroute = process_copilot_intent("Accept reroute please", sim_instance=sim_test)
    assert sim_test.active_route_id == "PROACTIVE_BYPASS", "Natural language should switch route"
    assert "Proactive Bypass Reroute Accepted" in reply_reroute, "Accept reply mismatch"
    print("  --> PASS: Natural language 'Accept reroute' successfully switches navigation path on engine!")

    print("\n" + "=" * 70)
    print("  ALL 6 MAPS VERIFICATION SUITES COMPLETED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
