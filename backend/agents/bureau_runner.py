"""
Multi-Agent Swarm Bureau Runner
Launches all 5 Fetch.ai uAgents in a unified local event loop.
"""

from uagents import Bureau
from .agent_junction import junction_agent
from .agent_ambulance import ambulance_agent
from .agent_triage import triage_agent
from .agent_pedestrian import pedestrian_agent
from .agent_asi_one import asi_one_agent

def create_swarm_bureau() -> Bureau:
    bureau = Bureau(endpoint="http://localhost:8000/submit", port=8000)
    bureau.add(junction_agent)
    bureau.add(ambulance_agent)
    bureau.add(triage_agent)
    bureau.add(pedestrian_agent)
    bureau.add(asi_one_agent)
    return bureau

def main():
    print("=" * 70)
    print("  TRAFFICFLOW-AI : FETCH.AI DECENTRALIZED MULTI-AGENT SWARM")
    print("  Built for FETCH-A-THON 3.0 & ASI:ONE AGENT CHALLENGE")
    print("=" * 70)
    print(f"  [1] Junction Controller Agent: {junction_agent.address}")
    print(f"  [2] 108 Emergency Fleet Agent: {ambulance_agent.address}")
    print(f"  [3] Triage CAD 108 Agent:      {triage_agent.address}")
    print(f"  [4] Pedestrian VRU Agent:      {pedestrian_agent.address}")
    print(f"  [5] ASI:One Gateway Agent:     {asi_one_agent.address}")
    print("=" * 70)
    print("  Starting Bureau Swarm Event Loop on port 8000...")
    
    bureau = create_swarm_bureau()
    bureau.run()

if __name__ == "__main__":
    main()
