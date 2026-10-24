"""
Agent: CommuterNavigationAgent
In-Vehicle / Smartphone Client Agent representing the driver.
Discovers local junction infrastructure via Agentverse Almanac and receives proactive reroute notices.
"""

from uagents import Agent, Context, Protocol
import time
from .models import (
    RouteCongestionQuery,
    ProactiveRerouteNotice,
    RerouteActionCommand
)

commuter_agent = Agent(
    name="commuter_navigation_agent",
    port=8011,
    seed="commuter_navigation_agent_seed_2026_metro_koramangala"
)

commuter_proto = Protocol(name="CommuterNavigationProtocol", version="1.0.0")

@commuter_proto.on_message(model=ProactiveRerouteNotice)
async def handle_proactive_reroute_notice(ctx: Context, sender: str, msg: ProactiveRerouteNotice):
    ctx.logger.info(f"[COMMUTER AGENT] 🔔 PROACTIVE ADVISORY RECEIVED from {sender}!")
    ctx.logger.info(f"                 Junction: {msg.junction_name} | Queue: {msg.current_queue_cars} cars")
    ctx.logger.info(f"                 Recommendation: {msg.turn_action_instruction}")
    ctx.logger.info(f"                 Time Saved: {msg.time_saved_minutes} mins | Fuel Saved: {msg.fuel_saved_liters} L")

    # In production, this renders the modal alert on the driver's in-car HUD / mobile map
    # Automatically prepares a confirmation command
    cmd = RerouteActionCommand(
        driver_id="COMMUTER-KA-01-MJ-8821",
        decision="ACCEPTED",
        chosen_route_id="PROACTIVE_BYPASS",
        timestamp=time.time()
    )
    ctx.logger.info(f"[COMMUTER AGENT] ✅ Auto-accepted bypass recommendation.")
    await ctx.send(sender, cmd)

commuter_agent.include(commuter_proto)

if __name__ == "__main__":
    commuter_agent.run()
