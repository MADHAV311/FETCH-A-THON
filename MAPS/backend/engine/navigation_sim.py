"""
TrafficFlow-MAPS: Navigation Simulation Engine
Simulates the real-time vehicle movement, GPS tracking, junction approach,
proactive alert triggering, and path branching (Default congested route vs Proactive bypass).
"""

import math
import time
from ..config import MAPS_CONFIG
from .route_optimizer import RouteOptimizer

class NavigationSim:
    def __init__(self):
        self.config = MAPS_CONFIG
        self.optimizer = RouteOptimizer()
        self.reset()

    def reset(self):
        self.is_playing = True
        self.sim_speed = 1.0
        self.sim_time = 0.0

        # Route Selection & Decision
        self.active_route_id = "DEFAULT_ROUTE"
        self.reroute_decision = "PENDING" # "PENDING", "ACCEPTED", "REJECTED"
        self.alert_triggered = False
        self.has_reached_destination = False

        # Live Bottleneck Junction Telemetry
        self.junction_queue = self.config["CENTRAL_JUNCTION"]["default_queue_cars"]
        self.junction_red_timer = self.config["CENTRAL_JUNCTION"]["red_phase_remaining_sec"]
        self.is_ambulance_preemption = True

        # Vehicle State
        start = self.config["ORIGIN"]
        self.veh_x = float(start["x"])
        self.veh_y = float(start["y"])
        self.veh_speed = self.config["VEHICLE"]["cruising_speed_px_sec"]
        self.veh_angle = 0.0

        self.current_waypoint_idx = 0
        self.trip_distance_traveled_px = 0.0
        self.trip_elapsed_time_sec = 0.0
        self.idle_wait_time_sec = 0.0
        self.fuel_consumed_liters = 0.0

        # Latest Optimizer Evaluation
        self.active_advisory = self.optimizer.evaluate_traffic_hurdle(
            current_queue=self.junction_queue,
            red_remaining=self.junction_red_timer,
            is_emergency=self.is_ambulance_preemption
        )

    def accept_reroute(self):
        """User accepts proactive diversion recommendation."""
        if self.reroute_decision == "ACCEPTED":
            return {"success": True, "message": "Already accepted"}

        self.reroute_decision = "ACCEPTED"
        self.active_route_id = "PROACTIVE_BYPASS"

        # Update waypoint index to follow bypass path seamlessly from current position
        waypoints = self.config["ROUTES"]["PROACTIVE_BYPASS"]["waypoints"]
        # Find closest waypoint ahead on bypass
        closest_idx = 2 # Diversion waypoint
        self.current_waypoint_idx = closest_idx

        return {
            "success": True,
            "decision": "ACCEPTED",
            "message": "Proactive Reroute Activated: Diverting to 8th Cross Green Wave Bypass",
            "activeRoute": self.active_route_id
        }

    def reject_reroute(self):
        """User rejects recommendation, staying on congested default route."""
        self.reroute_decision = "REJECTED"
        self.active_route_id = "DEFAULT_ROUTE"
        return {
            "success": True,
            "decision": "REJECTED",
            "message": "Staying on Default Route: Preparing for Central Junction delay",
            "activeRoute": self.active_route_id
        }

    def update(self, raw_dt: float):
        if not self.is_playing or self.has_reached_destination:
            return

        dt = min(0.1, raw_dt * self.sim_speed)
        self.sim_time += dt
        self.trip_elapsed_time_sec += dt

        # Slowly decrement junction red timer for realism
        if self.junction_red_timer > 0:
            self.junction_red_timer = max(0.0, self.junction_red_timer - (dt * 0.4))

        # Check proximity to the 8th Cross Diversion Point (x=320, y=380)
        div = self.config["DIVERSION_POINT"]
        dist_to_diversion = math.hypot(div["x"] - self.veh_x, div["y"] - self.veh_y)

        # Trigger proactive notification 200px (approx 350m) in advance!
        if dist_to_diversion < 180.0 and not self.alert_triggered and self.reroute_decision == "PENDING":
            self.alert_triggered = True

        # Determine target waypoint path
        route_spec = self.config["ROUTES"][self.active_route_id]
        waypoints = route_spec["waypoints"]

        if self.current_waypoint_idx >= len(waypoints):
            self.has_reached_destination = True
            self.veh_speed = 0.0
            return

        target_wp = waypoints[self.current_waypoint_idx]
        dx = target_wp["x"] - self.veh_x
        dy = target_wp["y"] - self.veh_y
        dist_to_wp = math.hypot(dx, dy)

        # Bottleneck behavior if user is on default route and approaching Central Junction (x=480, y=320)
        is_stuck_in_bottleneck = False
        if self.active_route_id == "DEFAULT_ROUTE":
            dist_to_junction = math.hypot(480 - self.veh_x, 320 - self.veh_y)
            # If within queue zone and signal is RED, vehicle gets stuck in queue
            if dist_to_junction < 110.0 and self.junction_red_timer > 5.0:
                is_stuck_in_bottleneck = True
                self.veh_speed = max(0.0, self.veh_speed - (self.config["VEHICLE"]["deceleration"] * dt))
                self.idle_wait_time_sec += dt
                # Fuel wasted idling: ~1.2 L/hr
                self.fuel_consumed_liters += (1.2 / 3600.0) * dt
            else:
                self.veh_speed = min(self.config["VEHICLE"]["cruising_speed_px_sec"], self.veh_speed + 20.0 * dt)
                self.fuel_consumed_liters += (0.6 / 3600.0) * dt
        else:
            # Bypass route is cruising smoothly at full speed!
            self.veh_speed = min(self.config["VEHICLE"]["cruising_speed_px_sec"] * 1.1, self.veh_speed + 25.0 * dt)
            self.fuel_consumed_liters += (0.55 / 3600.0) * dt

        # Move vehicle along vector if not stuck
        if not is_stuck_in_bottleneck and dist_to_wp > 6.0:
            self.veh_angle = math.atan2(dy, dx)
            step_dist = self.veh_speed * dt
            self.veh_x += math.cos(self.veh_angle) * step_dist
            self.veh_y += math.sin(self.veh_angle) * step_dist
            self.trip_distance_traveled_px += step_dist
        elif not is_stuck_in_bottleneck:
            # Reached waypoint, advance to next
            self.current_waypoint_idx += 1
            if self.current_waypoint_idx >= len(waypoints):
                self.has_reached_destination = True
                self.veh_speed = 0.0

        # Update active advisory metrics
        self.active_advisory = self.optimizer.evaluate_traffic_hurdle(
            current_queue=self.junction_queue,
            red_remaining=self.junction_red_timer,
            is_emergency=self.is_ambulance_preemption
        )

    def to_dict(self):
        return {
            "isPlaying": self.is_playing,
            "simSpeed": self.sim_speed,
            "simTime": round(self.sim_time, 1),
            "vehicle": {
                "x": round(self.veh_x, 1),
                "y": round(self.veh_y, 1),
                "speedKmh": round((self.veh_speed / self.config["VEHICLE"]["cruising_speed_px_sec"]) * 45.0, 1),
                "headingAngle": round(self.veh_angle, 2),
                "currentWaypointIndex": self.current_waypoint_idx,
                "hasReachedDestination": self.has_reached_destination
            },
            "navigation": {
                "activeRouteId": self.active_route_id,
                "rerouteDecision": self.reroute_decision,
                "alertTriggered": self.alert_triggered,
                "tripElapsedSec": round(self.trip_elapsed_time_sec, 1),
                "idleWaitSec": round(self.idle_wait_time_sec, 1),
                "fuelConsumedLiters": round(self.fuel_consumed_liters, 3),
                "distanceTraveledPx": round(self.trip_distance_traveled_px, 1)
            },
            "advisory": self.active_advisory,
            "junction": {
                "name": self.config["CENTRAL_JUNCTION"]["name"],
                "queue": self.junction_queue,
                "redPhaseRemaining": round(self.junction_red_timer, 1),
                "signalState": "RED" if self.junction_red_timer > 0 else "GREEN",
                "isEmergency": self.is_ambulance_preemption
            }
        }
