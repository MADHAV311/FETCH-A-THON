# TrafficFlow-MAPS: Signal-Aware Proactive Navigation & Multi-Agent Commuter Rerouting Copilot
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![Framework: Fetch.ai uAgents](https://img.shields.io/badge/Framework-Fetch.ai_uAgents-00D26A?logo=fetch.ai)
![Protocol: Agent Chat Protocol (ACP v0.3.0)](https://img.shields.io/badge/Protocol-Agent_Chat_Protocol_(ACP)-7952DE)
![Platform: ASI:One & Agentverse](https://img.shields.io/badge/Platform-ASI%3AOne_%26_Agentverse-FF6B6B)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue)

> 🏆 **Built for FETCH-A-THON 3.0 & ASI:ONE AGENT CHALLENGE** | Presidency University, Bengaluru  
> *Organized by Fetch.ai, Innovation Lab by Fetch.ai, ASI:ONE (Artificial Superintelligence Alliance), and Masters' Union*  
> **Team ID:** `FETCHATHON3.0-8799` | **Team Lead:** BANDILA MADHAV | **Members:** LAKSHMI REDDY M S, KEERTHIPATI SATHYASREE, KHAMITHKAR SUPRITHA

---

## 🌟 The Core Problem with Standard Google Maps

When motorists navigate metropolitan Indian cities using standard Google Maps or Apple Maps:
1. **Google Maps is Reactive, NOT Predictive:** It only turns a road **RED** *after* 30–50 vehicles have already come to a complete standstill and their phone GPS speeds drop to 0 km/h.
2. **Google Maps is Blind to Traffic Signals:** Google Maps has zero Vehicle-to-Infrastructure (V2I) connection to the traffic light ahead. It cannot tell you that an intersection has a 34-car queue with 44 seconds of Red light remaining or an active 108 Ambulance preemption.
3. **The Trap:** By the time Google Maps detects the red line or offers a detour, **the driver is already stuck at the back of the queue** and cannot turn anymore.

---

## 🚀 The TrafficFlow-MAPS Solution

**TrafficFlow-MAPS** connects the commuter's navigation directly to the physical smart traffic light via **Fetch.ai Decentralized Multi-Agents (`uagents`)**, **Agentverse Almanac**, and **ASI:One (ACP v0.3.0)**:

* **350m Proactive Horizon:** 350 meters *before* reaching the bottleneck—right before the last available diversion turn (8th Cross Bypass)—the driver's in-car agent queries the junction agent.
* **Proactive Slide-Down Reroute Alert:** The navigation pops up an interactive alert:
  > *"⚠️ Upcoming Bottleneck at Central Junction: 34 cars queued • 44s Red Light remaining • 108 Ambulance preemption active.*  
  > *💡 Proactive Recommendation: Take Right Turn at 8th Cross (150m ahead) onto Ring Bypass.*  
  > *⏱️ Saves 6.2 mins • ⛽ Saves 0.42L Fuel • ₹58.55 Trip Savings.*  
  > **[ ACCEPT PROACTIVE BYPASS ]**  **[ STAY ON CONGESTED ROUTE ]**"
* **Dynamic Path Switching:** 
  * If accepted: The car turns right onto the emerald green bypass and glides through the synchronized green wave corridor.
  * If rejected: The car continues straight, joins the 34-car red light queue, idles, and incurs a 7.7-minute delay.

---

## 🤖 Decentralized Multi-Agent Swarm (MAS) Architecture

```
                       ┌──────────────────────────────────────────────┐
                       │          ASI:ONE (asi1.ai) / Voice           │
                       │  "Hey ASI, route me to Tech Park. Skip jams" │
                       └──────────────────────┬───────────────────────┘
                                              │ Agent Chat Protocol (ACP v0.3.0)
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │             AGENTVERSE ALMANAC               │
                       │  Discovers nearby Junction Agents by GPS     │
                       │  Proxy routing via Agentverse Mailbox        │
                       └──────────────────────┬───────────────────────┘
                                              │ Peer-to-Peer A2A Protocol
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │           FETCH.AI uAGENTS SWARM             │
                       │  • CommuterDriverAgent (In-Vehicle Unit)     │
                       │  • JunctionSignalHubAgent (Physical Pole)    │
                       │  • AlmanacGPSResolverAgent (GPS Resolver)    │
                       │  • ASIOneNavigationCopilot (ACP Copilot)     │
                       └──────────────────────────────────────────────┘
```

### The 4 Autonomous Agents:
| Agent Name | Port | Role & Autonomous Action | Cryptographic Identity |
| :--- | :---: | :--- | :--- |
| **1. CommuterDriverAgent** | `8011` | In-vehicle smartphone/car navigation client. Continuously tracks GPS position and handles reroute actions. | `agent1qvwv2a00w8x5h7l9m2n4p6q8s0t2u4v6w8x0y2z` |
| **2. JunctionSignalHubAgent** | `8012` | Edge agent embedded at the physical intersection pole. Monitors queue count and emits proactive warnings. | `agent1q2z8k6x0w3h8f8j9s7l2m4n5p6q7r8s9t0u1v2w` |
| **3. AlmanacGPSResolverAgent** | `8013` | Decentralized DNS resolver. Maps driver $(lat, lng)$ coordinates to the nearest smart junction agent. | `agent1qt7y9x1w3v5u7t9s1r3q5p7o9n1m3l5k7j9h1g` |
| **4. ASIOneNavigationCopilot** | `8010` | Public conversational agent implementing ACP v0.3.0 on [asi1.ai](https://asi1.ai) and Agentverse (`@trafficflow-maps`). | `agent1qwmawnyywfmhxgtyfl6uut9gkv4s36q4ykw220trle6053c4k8nrzvp98t4` |

---

## 💬 Natural Language Intent-to-Action (ASI:One ACP v0.3.0)

Using the official Agent Chat Protocol, commuters can interact with their in-car copilot via voice or chat:
* *"Is there traffic ahead on my route?"* $\rightarrow$ Returns live queue depth (34 cars) and red timer (44s).
* *"Why should I divert onto 8th Cross?"* $\rightarrow$ Explains 108 Ambulance preemption and 6.2-minute delay delta.
* *"Accept reroute"* $\rightarrow$ Dynamically switches navigation path to 8th Cross Green Wave Bypass.
* *"What are my fuel savings?"* $\rightarrow$ Displays MoRTH economic breakdown (0.42L saved, ₹58.55 net trip value).

---

## 🏛️ Indian Smart City & MoRTH Economic Impact

Grounded in Indian Ministry of Road Transport and Highways (MoRTH) urban benchmarks:
* **Fuel Cost:** ₹102.50 / Liter
* **Commuter Time Value:** ₹150.00 / Hour
* **Single Commuter Bypass Savings:**
  * **Delay Avoided:** **6.2 minutes**
  * **Fuel Saved:** **0.42 Liters** (₹43.05)
  * **Commuter Time Value Saved:** **₹15.50**
  * **Total Net Savings:** **₹58.55 per vehicle**
  * **CO₂ Abatement:** **0.97 kg**
* **Corridor Annualized Impact (18,500 daily commuters):**
  * **Annual Fuel Saved:** **2.33 Million Liters**
  * **Annual CO₂ Abatement:** **5,380 Metric Tonnes**
  * **Annual Economic Value:** **₹324.9 Lakhs / Year**

---

## 📍 Pinpoint Exact Bottleneck Localization
When congestion is detected, TrafficFlow-MAPS does not merely state that an area has traffic—it pinpoints **EXACTLY where the bottleneck is**, down to physical milestones, queue stretches, and affected lanes:
* **📌 Epicenter Landmark:** Physical stopline, intersection corner, or metro pillar (e.g., *North Arterial Corridor at Central Junction Stopline, directly opposite Metro Pillar #412*).
* **📏 Upstream Backlog Stretch:** Exact length of the queue in meters and upstream anchor (e.g., *350 meters upstream from the stopline back to 8th Cross Diversion junction*).
* **🚗 Blocked / Affected Lanes:** Specific lane designations (e.g., *Inbound Left & Center Through-Lanes immobilized; Right-turn pocket crawling at 4 km/h*).
* **🌐 GPS Span Coordinates:** Exact start and finish coordinates of the queue (e.g., `12.9195° N, 77.6360° E (Queue Tail) ➔ 12.9172° N, 77.6385° E (Stopline)`).
* **🗺️ Visual Map Overlay:** The 2D cyber-navigation map displays the animated hazard-hatched 350m congestion zone with milestone tags and stopline indicators.

---

## 🚀 How to Run the Prototype

### 1. Launch the Application Server:
```powershell
& "C:\MADHAV\FETCH-A-THON\PS1\.venv\Scripts\python.exe" "C:\MADHAV\FETCH-A-THON\MAPS\run.py"
```
* **Interactive Navigation Dashboard:** `http://localhost:8085`
* **Real-Time Telemetry API:** `http://localhost:8085/api/nav/state`

### 2. Run the Automated Verification Suite:
```powershell
& "C:\MADHAV\FETCH-A-THON\PS1\.venv\Scripts\python.exe" "C:\MADHAV\FETCH-A-THON\MAPS\test_maps.py"
```

### 3. Launch the Multi-Agent Bureau (Port 8010):
```powershell
& "C:\MADHAV\FETCH-A-THON\PS1\.venv\Scripts\python.exe" "C:\MADHAV\FETCH-A-THON\MAPS\backend\agents\bureau_runner.py"
```

### 4. Deploy to Agentverse Cloud (60 Seconds):
1. Log in to [https://agentverse.ai](https://agentverse.ai).
2. Create a **New Blank Agent**.
3. Copy and paste the contents of [`backend/agents/agentverse_hosted.py`](backend/agents/agentverse_hosted.py).
4. Click **Start** to register the agent on the Fetch.ai Almanac and enable ACP discovery on [asi1.ai](https://asi1.ai).
