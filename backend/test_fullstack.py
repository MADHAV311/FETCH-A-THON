import sys
import os
import time
import json
import urllib.request
import urllib.parse

PORT = 8080
BASE_URL = f"http://127.0.0.1:{PORT}"

def run_tests():
    print("[TEST] 1. Checking root endpoint GET /")
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req, timeout=5) as res:
        assert res.status == 200, f"Expected 200, got {res.status}"
        body = res.read().decode("utf-8")
        assert "AI Adaptive Traffic Signal Digital Twin" in body, "Expected title in HTML"
        assert "situation-modes-bar" in body, "Expected situation-modes-bar in HTML"
        assert 'data-mode="AMBULANCE"' in body, "Expected AMBULANCE mode button in HTML"
        assert 'data-mode="SEVERE_ACCIDENT"' in body, "Expected SEVERE_ACCIDENT button in HTML"
        assert 'data-mode="MINOR_ACCIDENT"' in body, "Expected MINOR_ACCIDENT button in HTML"
        assert 'data-mode="PEDESTRIAN_SCRAMBLE"' in body, "Expected PEDESTRIAN_SCRAMBLE button in HTML"
        assert 'data-mode="MULTI_INTERSECTION"' in body, "Expected MULTI_INTERSECTION button in HTML"
        assert "viewport-top-hud" in body, "Expected viewport-top-hud in HTML"
        assert "pole-card-a" in body, "Expected pole-card-a in HTML"
        assert "accident-cad-card" in body, "Expected accident-cad-card in HTML"
        assert "Trauma Care & Emergency Center" in body, "Expected Trauma Care Center in HTML"
        assert "₹" in body, "Expected Indian Rupee symbol in HTML"
        print("  --> PASS: index.html served with all 5 Pillars and Situation Modes!")

    print("\n[TEST] 2. Checking Static Assets")
    for asset in [
        "/css/main.css",
        "/css/dashboard.css",
        "/css/simulation.css",
        "/css/charts.css",
        "/js/app.js",
        "/js/config.js",
        "/js/api/ApiClient.js",
        "/js/ui/DashboardUI.js",
        "/js/ui/AudioEffects.js",
        "/js/rendering/Renderer.js",
        "/js/rendering/ChartRenderer.js"
    ]:
        req = urllib.request.Request(f"{BASE_URL}{asset}")
        with urllib.request.urlopen(req, timeout=5) as res:
            assert res.status == 200, f"Expected 200 for {asset}, got {res.status}"
        print(f"  --> PASS: {asset} (200 OK)")

    print("\n[TEST] 3. Checking GET /api/state Structure & Indian Smart City Economics")
    req = urllib.request.Request(f"{BASE_URL}/api/state")
    with urllib.request.urlopen(req, timeout=5) as res:
        assert res.status == 200
        state = json.loads(res.read().decode("utf-8"))
        assert "accidentState" in state, "Missing accidentState"
        assert "multiIntersection" in state, "Missing multiIntersection"
        assert "simAdaptive" in state, "Missing simAdaptive"
        assert "comparisonStats" in state, "Missing comparisonStats"
        adaptive = state["simAdaptive"]
        assert "directionalSirens" in adaptive, "Missing directionalSirens"
        assert "pedestrians" in adaptive, "Missing pedestrians"
        stats = state["comparisonStats"]
        assert "rupeesSaved" in stats, "Missing rupeesSaved in stats"
        assert "annualRupeesSavedLakhs" in stats, "Missing annualRupeesSavedLakhs in stats"
        assert "timeValueSavedInr" in stats, "Missing timeValueSavedInr in stats"
        assert "fuelValueSavedInr" in stats, "Missing fuelValueSavedInr in stats"
        print(f"  --> PASS: /api/state contains all required Indian Smart City metrics.")
        print(f"      rupeesSaved: INR {stats['rupeesSaved']}, Annual: INR {stats['annualRupeesSavedLakhs']} Lakhs/yr")

    print("\n[TEST] 4. Testing Situation Mode: AMBULANCE (North Pole Siren & 108 Preemption)")
    post_data = json.dumps({"mode": "AMBULANCE"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/situation/mode", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as res:
        resp = json.loads(res.read().decode("utf-8"))
        assert resp["success"] == True
        print(f"  --> PASS: {resp}")
        time.sleep(0.5)
        with urllib.request.urlopen(f"{BASE_URL}/api/state") as sres:
            sdata = json.loads(sres.read().decode("utf-8"))
            sirens = sdata["simAdaptive"].get("directionalSirens", {})
            active_sirens = [k for k, v in sirens.items() if v.get("active")]
            print(f"      Active Pole Sirens: {active_sirens}")
            assert "A" in active_sirens, "Expected Pole A (North) siren to be active for oncoming ambulance"

    print("\n[TEST] 5. Testing Situation Mode: SEVERE_ACCIDENT (6.8G Crash -> Auto 108 CAD Call + Trauma Care Center)")
    post_data = json.dumps({"mode": "SEVERE_ACCIDENT"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/situation/mode", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as res:
        resp = json.loads(res.read().decode("utf-8"))
        assert resp["success"] == True
        print(f"  --> PASS: {resp}")
        time.sleep(0.5)
        with urllib.request.urlopen(f"{BASE_URL}/api/state") as sres:
            sdata = json.loads(sres.read().decode("utf-8"))
            acc_state = sdata.get("accidentState", {})
            acc = acc_state.get("activeAccident", {})
            hosp = acc.get("hospital", {})
            print(f"      Accident Active:   {acc_state.get('hasActiveAccident')}")
            print(f"      Classification:    {acc.get('classification')}")
            print(f"      Hospital Call:     {acc.get('callEmergency')} ({hosp.get('name')})")
            print(f"      GPS Coordinates:   {hosp.get('gps')}")
            print(f"      CAD Dispatch Code: {hosp.get('dispatchCode')}")
            print(f"      Traffic Action:    {acc.get('trafficAction')}")
            assert acc_state.get("hasActiveAccident") == True
            assert acc.get("classification") == "CRITICAL_EMERGENCY"
            assert acc.get("callEmergency") == True
            assert "Trauma Care" in hosp.get("name")
            assert "LOCKDOWN" in acc.get("trafficAction")

    print("\n[TEST] 6. Testing Situation Mode: MINOR_ACCIDENT (1.3G Scrape -> AI Decides NOT to Call 108)")
    post_data = json.dumps({"mode": "MINOR_ACCIDENT"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/situation/mode", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as res:
        resp = json.loads(res.read().decode("utf-8"))
        assert resp["success"] == True
        print(f"  --> PASS: {resp}")
        time.sleep(0.5)
        with urllib.request.urlopen(f"{BASE_URL}/api/state") as sres:
            sdata = json.loads(sres.read().decode("utf-8"))
            acc_state = sdata.get("accidentState", {})
            acc = acc_state.get("activeAccident", {})
            print(f"      Accident Active:       {acc_state.get('hasActiveAccident')}")
            print(f"      Classification:        {acc.get('classification')}")
            print(f"      108 Call Dispatched:   {acc.get('callEmergency')}")
            print(f"      CAD Status:            {acc.get('cadStatus')}")
            print(f"      Suppression Rationale: {acc.get('triageReason')}")
            assert acc_state.get("hasActiveAccident") == True
            assert acc.get("classification") == "MINOR_FENDER_BENDER"
            assert acc.get("callEmergency") == False, "CRITICAL REQUIREMENT VIOLATED: Minor accident must NOT call hospital!"
            assert "DO NOT CALL 108" in acc.get("triageReason") or "bandwidth" in acc.get("triageReason").lower()

    print("\n[TEST] 7. Testing Accident Clear API")
    post_data = json.dumps({}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/accident/clear", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as res:
        resp = json.loads(res.read().decode("utf-8"))
        assert resp["success"] == True
        print("  --> PASS: Accident cleared successfully")
        with urllib.request.urlopen(f"{BASE_URL}/api/state") as sres:
            sdata = json.loads(sres.read().decode("utf-8"))
            assert sdata.get("accidentState", {}).get("hasActiveAccident") == False

    print("\n[TEST] 8. Testing Situation Mode: PEDESTRIAN_SCRAMBLE (Barnes Dance Phase)")
    post_data = json.dumps({"mode": "PEDESTRIAN_SCRAMBLE"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/situation/mode", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as res:
        resp = json.loads(res.read().decode("utf-8"))
        assert resp["success"] == True
        print(f"  --> PASS: {resp}")
        time.sleep(0.5)
        with urllib.request.urlopen(f"{BASE_URL}/api/state") as sres:
            sdata = json.loads(sres.read().decode("utf-8"))
            adaptive = sdata.get("simAdaptive", {})
            peds = adaptive.get("pedestrians", {})
            scramble = adaptive.get("scrambleActive", False) or peds.get("scrambleActive", False)
            print(f"      Scramble Active: {scramble}")
            assert scramble == True

    print("\n[TEST] 9. Testing Situation Mode: MULTI_INTERSECTION (Arterial Green Wave Corridor)")
    post_data = json.dumps({"mode": "MULTI_INTERSECTION"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/situation/mode", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as res:
        resp = json.loads(res.read().decode("utf-8"))
        assert resp["success"] == True
        print(f"  --> PASS: {resp}")
        with urllib.request.urlopen(f"{BASE_URL}/api/state") as sres:
            sdata = json.loads(sres.read().decode("utf-8"))
            corridor = sdata.get("multiIntersection", {})
            assert "nodes" in corridor
            node_names = [n["name"] for n in corridor["nodes"]]
            print(f"      Corridor Name:         {corridor.get('corridorName')}")
            print(f"      Corridor Nodes:        {node_names}")
            print(f"      Coordinated Bandwidth: {corridor['metrics'].get('greenWaveBandwidthSec')}s")
            print(f"      Wave Coherence:        {corridor['metrics'].get('greenWaveCoherencePct')}%")
            assert len(corridor["nodes"]) == 3

    print("\n[TEST] 10. Testing Situation Mode: CRIME_CRITICAL (Armed Assault -> Auto 112 Police CAD Call)")
    post_data = json.dumps({"mode": "CRIME_CRITICAL"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/situation/mode", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as res:
        resp = json.loads(res.read().decode("utf-8"))
        assert resp["success"] == True
        time.sleep(0.5)
        with urllib.request.urlopen(f"{BASE_URL}/api/state") as sres:
            sdata = json.loads(sres.read().decode("utf-8"))
            crime = sdata.get("crimeState", {}).get("activeCrime", {})
            print(f"      Classification:    {crime.get('classification')}")
            print(f"      Call Police 112:   {crime.get('callPolice')}")
            print(f"      Station:           {crime.get('police', {}).get('station')}")
            print(f"      Weapon Detected:   {crime.get('weaponDetected')}")
            print(f"      Traffic Action:    {crime.get('trafficAction')}")
            assert crime.get("callPolice") == True
            assert crime.get("classification") == "CRITICAL_ARMED_ASSAULT"
            assert "Central City Police" in crime.get("police", {}).get("station", "")

    print("\n[TEST] 11. Testing Situation Mode: CRIME_MINOR (Verbal Dispute -> AI Suppresses Police 112 Call)")
    post_data = json.dumps({"mode": "CRIME_MINOR"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/situation/mode", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as res:
        resp = json.loads(res.read().decode("utf-8"))
        assert resp["success"] == True
        time.sleep(0.5)
        with urllib.request.urlopen(f"{BASE_URL}/api/state") as sres:
            sdata = json.loads(sres.read().decode("utf-8"))
            crime = sdata.get("crimeState", {}).get("activeCrime", {})
            print(f"      Classification:    {crime.get('classification')}")
            print(f"      Call Police 112:   {crime.get('callPolice')}")
            print(f"      Suppression Rationale: {crime.get('triageReason')}")
            assert crime.get("callPolice") == False
            assert "DO NOT CALL POLICE" in crime.get("triageReason") or "bandwidth" in crime.get("triageReason").lower()

    print("\n[TEST] 12. Testing Situation Mode: SCHOOL_SMALL_GROUP (2 Students, 0 Inflow -> Immediate Red & 8s Walk)")
    post_data = json.dumps({"mode": "SCHOOL_SMALL_GROUP"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/situation/mode", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as res:
        resp = json.loads(res.read().decode("utf-8"))
        assert resp["success"] == True
        time.sleep(0.5)
        with urllib.request.urlopen(f"{BASE_URL}/api/state") as sres:
            sdata = json.loads(sres.read().decode("utf-8"))
            peds = sdata.get("simAdaptive", {}).get("pedestrians", {})
            sz = peds.get("schoolZone", {})
            print(f"      School Zone Active: {sz.get('active')}")
            print(f"      Scenario:           {sz.get('scenario')}")
            print(f"      Curb Waiting:       {sz.get('curbWaiting')}")
            print(f"      Trailing Inflow:    {sz.get('trailingInflow')}")
            print(f"      Crossing Window:    {sz.get('crossingWindow')}s")
            assert sz.get("active") == True
            assert sz.get("curbWaiting") == 2
            assert sz.get("trailingInflow") == 0
            assert sz.get("crossingWindow") == 8.0

    print("\n[TEST] 13. Testing Situation Mode: SCHOOL_PLATOON_INFLOW (10 Students + 6 Approaching -> 4s Aggregation Hold -> 18s Scramble)")
    post_data = json.dumps({"mode": "SCHOOL_PLATOON_INFLOW"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/situation/mode", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as res:
        resp = json.loads(res.read().decode("utf-8"))
        assert resp["success"] == True
        time.sleep(0.5)
        with urllib.request.urlopen(f"{BASE_URL}/api/state") as sres:
            sdata = json.loads(sres.read().decode("utf-8"))
            peds = sdata.get("simAdaptive", {}).get("pedestrians", {})
            sz = peds.get("schoolZone", {})
            print(f"      School Zone Active: {sz.get('active')}")
            print(f"      Scenario:           {sz.get('scenario')}")
            print(f"      Curb Waiting:       {sz.get('curbWaiting')}")
            print(f"      Trailing Inflow:    {sz.get('trailingInflow')}")
            print(f"      Aggregation Timer:  {sz.get('aggregationTimer')}s")
            print(f"      Decision:           {sz.get('cvDecision')}")
            assert sz.get("active") == True
            assert sz.get("curbWaiting") == 10
            assert sz.get("trailingInflow") == 6

    print("\n[TEST] 14. Testing Normal Flow Restoration")
    post_data = json.dumps({"mode": "NORMAL"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/situation/mode", data=post_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as res:
        resp = json.loads(res.read().decode("utf-8"))
        assert resp["success"] == True
        print("  --> PASS: Restored to NORMAL flow")

    print("\n========================================================")
    print("  ALL 14 VERIFICATION SUITES COMPLETED WITH 100% SUCCESS!")
    print("========================================================")

if __name__ == "__main__":
    run_tests()
