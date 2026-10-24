"""
TrafficFlow-MAPS: REST API Request Handlers
Dispatches incoming HTTP requests to the Navigation Simulation and ASI:One Copilot Agent.
"""

import json
from ..agents.agent_asione_copilot import process_copilot_intent

def api_response(data, status=200, content_type="application/json"):
    return {
        "status": status,
        "content_type": content_type,
        "body": json.dumps(data)
    }

def handle_get_state(sim):
    return api_response(sim.to_dict())

def handle_reroute_accept(sim):
    result = sim.accept_reroute()
    return api_response(result)

def handle_reroute_reject(sim):
    result = sim.reject_reroute()
    return api_response(result)

def handle_control(sim, payload):
    action = payload.get("action", "play")
    if action == "play":
        sim.is_playing = True
    elif action == "pause":
        sim.is_playing = False
    elif action == "reset":
        sim.reset()
    elif action == "speed":
        sim.sim_speed = float(payload.get("speed", 1.0))

    return api_response({"success": True, "action": action, "isPlaying": sim.is_playing, "speed": sim.sim_speed})

def handle_asione_chat(sim, payload):
    query = payload.get("message", "").strip()
    if not query:
        return api_response({"error": "Empty message"}, status=400)

    # Process intent through the ASI:One Agent Chat Protocol logic
    agent_reply = process_copilot_intent(query, sim_instance=sim)

    return api_response({
        "success": True,
        "userQuery": query,
        "agentReply": agent_reply,
        "simState": sim.to_dict()
    })
