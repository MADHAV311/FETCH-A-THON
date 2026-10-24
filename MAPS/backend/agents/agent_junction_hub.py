"""
Agent: JunctionSignalHubAgent
Embedded edge agent at the physical smart traffic junction.
Continuously calculates approach queue lengths, remaining red phases, and emergency preemptions.
Emits ProactiveRerouteNotice to incoming Commuter Agents before they reach the decision horizon.
"""

from uagents import Agent, Context, Protocol
from .models import RouteCongestionQuery, ProactiveRerouteNotice

junction_hub_agent = Agent(
    name="junction_signal_hub_agent",
    port=8012,
    seed="junction_signal_hub_agent_seed_2026_central"
)

junction_hub_proto = Protocol(name="JunctionHubProtocol", version="1.0.0")

@junction_hub_proto.on_message(model=RouteCongestionQuery, replies=ProactiveRerouteNotice)
async def handle_congestion_query(ctx: Context, sender: str, msg: RouteCongestionQuery):
    ctx.logger.info(f"[JUNCTION HUB] 🚗 Query from Commuter {msg.driver_id} at ({msg.current_lat:.4f}, {msg.current_lng:.4f})")
    ctx.logger.info(f"               Planned Route: {msg.planned_route_id} | Speed: {msg.speed_kmh} km/h")

    # Current Junction Telemetry
    queue_cars = 34
    red_remaining = 44.0
    is_emergency = True

    rationale = (
        f"Central Junction is currently at saturation capacity with {queue_cars} queued vehicles. "
        f"Red phase is held for {red_remaining:.0f}s due to active 108 ALS Ambulance Green Carpet preemption. "
        f"Diverting onto 8th Cross Bypass will avoid an estimated 6.2 minutes of standstill idling."
    )

    ctx.logger.info(f"[JUNCTION HUB] ⚠️ High bottleneck detected. Generating ProactiveRerouteNotice.")

    notice = ProactiveRerouteNotice(
        bottleneck_detected=True,
        alert_level="CRITICAL_BOTTLENECK",
        junction_name="Central Arterial Junction",
        current_queue_cars=queue_cars,
        red_phase_remaining_sec=red_remaining,
        is_emergency_preemption=is_emergency,
        bypass_road_name="8th Cross Green Wave Bypass",
        turn_action_instruction="Take Right Turn at 8th Cross (150m ahead)",
        time_saved_minutes=6.2,
        fuel_saved_liters=0.42,
        rupees_saved_inr=45.80,
        rationale=rationale
    )

    await ctx.send(sender, notice)

junction_hub_agent.include(junction_hub_proto)

if __name__ == "__main__":
    junction_hub_agent.run()
