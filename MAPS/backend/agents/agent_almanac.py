"""
Agent: AlmanacGPSResolverAgent
Simulates the Fetch.ai Almanac Decentralized Registry for urban physical infrastructure.
Resolves geographic coordinates into registered Smart Junction Agent cryptographic addresses.
"""

from uagents import Agent, Context, Protocol
from .models import AlmanacLookupRequest, AlmanacLookupResponse

almanac_agent = Agent(
    name="almanac_gps_resolver_agent",
    port=8013,
    seed="almanac_gps_resolver_agent_seed_2026_metro"
)

almanac_proto = Protocol(name="AlmanacGPSResolverProtocol", version="1.0.0")

@almanac_proto.on_message(model=AlmanacLookupRequest, replies=AlmanacLookupResponse)
async def handle_almanac_lookup(ctx: Context, sender: str, msg: AlmanacLookupRequest):
    ctx.logger.info(f"[ALMANAC AGENT] 🛰️ GPS Resolution query for ({msg.query_lat}, {msg.query_lng})")

    # In a full deployment, this queries the on-chain Fetch.ai Almanac smart contract
    response = AlmanacLookupResponse(
        matched_agent_name="junction_signal_hub_agent",
        matched_agent_address="agent1q2z8k6x0w3h8f8j9s7l2m4n5p6q7r8s9t0u1v2w3x4y5z",
        distance_meters=340.0,
        status="ONLINE_ACTIVE"
    )

    ctx.logger.info(f"[ALMANAC AGENT] ✅ Matched Smart Junction Agent: {response.matched_agent_name}")
    await ctx.send(sender, response)

almanac_agent.include(almanac_proto)

if __name__ == "__main__":
    almanac_agent.run()
