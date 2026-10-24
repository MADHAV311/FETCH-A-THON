"""
TrafficFlow-MAPS: Multi-Agent Bureau Runner
Runs all 4 navigation micro-agents concurrently in an asynchronous Fetch.ai Bureau event loop.
"""

from uagents import Bureau
from .agent_commuter import commuter_agent
from .agent_junction_hub import junction_hub_agent
from .agent_almanac import almanac_agent
from .agent_asione_copilot import asione_copilot_agent

def create_maps_bureau() -> Bureau:
    bureau = Bureau(endpoint="http://localhost:8010/submit", port=8010)
    bureau.add(commuter_agent)
    bureau.add(junction_hub_agent)
    bureau.add(almanac_agent)
    bureau.add(asione_copilot_agent)
    return bureau

def main():
    print("=" * 70)
    print("  TRAFFICFLOW-MAPS : MULTI-AGENT PROACTIVE NAVIGATION SWARM")
    print("  Built for FETCH-A-THON 3.0 & ASI:ONE AGENT CHALLENGE")
    print("=" * 70)
    print(f"  [1] Commuter Driver Agent:     {commuter_agent.address}")
    print(f"  [2] Junction Signal Hub Agent: {junction_hub_agent.address}")
    print(f"  [3] Almanac GPS Resolver Agent:{almanac_agent.address}")
    print(f"  [4] ASI:One Copilot Agent:     {asione_copilot_agent.address}")
    print("=" * 70)
    print("  Starting Bureau Swarm Event Loop on port 8010...")

    bureau = create_maps_bureau()
    bureau.run()

if __name__ == "__main__":
    main()
