"""
AI Adaptive Traffic Signal Digital Twin - Vehicle Entity (Backend Service Layer)
Implements Intelligent Driver Model (IDM) car-following kinematics, braking, smooth turning,
and precise orientation vector calculation matching real-world right-hand traffic rules.
"""

import math
from .config import SIM_CONFIG

_global_vehicle_counter = 1

class Vehicle:
    def __init__(self, spec):
        global _global_vehicle_counter
        self.id = spec.get("id") or f"V-{_global_vehicle_counter}"
        _global_vehicle_counter += 1

        self.type_key = spec.get("type_key", "SEDAN")
        self.type_spec = SIM_CONFIG["VEHICLE_TYPES"].get(self.type_key, SIM_CONFIG["VEHICLE_TYPES"]["SEDAN"])
        self.road_id = spec["road_id"]              # 'A', 'B', 'C', 'D'
        self.lane_index = spec.get("lane_index", 0) # 0: outer curb lane, 1: inner lane
        self.intended_maneuver = spec.get("intended_maneuver", "STRAIGHT")
        
        self.length = self.type_spec["length"]
        self.width = self.type_spec["width"]
        self.color = spec.get("color") or self.type_spec["colors"][0]
        self.is_emergency = bool(self.type_spec.get("isEmergency", False))
        self.emergency_type = self.type_spec.get("emergencyType", "AMBULANCE" if self.is_emergency else None)

        self.max_speed = self.type_spec["maxSpeed"]
        self.accel = self.type_spec["accel"]
        self.decel = self.type_spec["decel"]
        self.speed = spec.get("initial_speed", self.max_speed * 0.75)

        self.s = spec.get("s", 0.0)
        self.total_approach_distance = SIM_CONFIG["SPAWN_OFFSET"]
        self.stop_line_s = self.total_approach_distance - SIM_CONFIG["STOP_LINE_OFFSET"]

        self.has_crossed_stop_line = False
        self.is_inside_intersection = False
        self.has_exited = False

        self.spawn_time = spec.get("spawn_time", 0.0)
        self.wait_time = 0.0
        self.is_stopped = False
        self.total_distance_traveled = 0.0
        self.clearance_time = None

        self.brake_lights_on = False
        self.turn_signal_timer = 0.0
        self.turn_signal_on = False
        self.siren_phase = 0.0

        self.x = 0.0
        self.y = 0.0
        self.angle = 0.0

        self.compute_world_transform()

    def update(self, dt, lead_vehicle, signal_state, current_time):
        if self.has_exited:
            return

        if self.speed < 4.0:
            self.wait_time += dt
            self.is_stopped = True
        else:
            self.is_stopped = False

        desired_accel = self.calculate_idm_acceleration(lead_vehicle, signal_state)
        self.speed = max(0.0, self.speed + desired_accel * dt)
        self.brake_lights_on = desired_accel < -15.0 or self.is_stopped

        ds = self.speed * dt
        self.s += ds
        self.total_distance_traveled += ds

        if not self.has_crossed_stop_line and self.s >= self.stop_line_s:
            self.has_crossed_stop_line = True
            self.is_inside_intersection = True

        exit_threshold = self.total_approach_distance + 350.0
        if self.s >= exit_threshold:
            self.has_exited = True
            self.is_inside_intersection = False
            if self.clearance_time is None:
                self.clearance_time = current_time

        if self.intended_maneuver != "STRAIGHT":
            self.turn_signal_timer += dt
            if self.turn_signal_timer > 0.35:
                self.turn_signal_timer = 0.0
                self.turn_signal_on = not self.turn_signal_on

        if self.is_emergency:
            self.siren_phase = (self.siren_phase + dt * 10.0) % (math.pi * 2.0)

        self.compute_world_transform()

    def calculate_idm_acceleration(self, lead_vehicle, signal_state):
        v = self.speed
        v0 = self.max_speed
        a = self.accel
        b = self.decel
        s0 = SIM_CONFIG["STANDSTILL_GAP"]
        T = SIM_CONFIG["TIME_HEADWAY"]

        free_road_term = a * (1.0 - (v / v0) ** 4)

        interaction_term = 0.0
        if lead_vehicle and lead_vehicle.s > self.s:
            gap = (lead_vehicle.s - lead_vehicle.length) - self.s
            delta_v = v - lead_vehicle.speed
            s_star = s0 + max(0.0, v * T + (v * delta_v) / (2.0 * math.sqrt(a * b)))
            interaction_term = -a * ((s_star / max(gap, 0.5)) ** 2)

        signal_term = 0.0
        if not self.has_crossed_stop_line:
            dist_to_stop = self.stop_line_s - self.s
            if dist_to_stop > -5.0:
                must_stop = False
                if signal_state in (SIM_CONFIG["SIGNAL_STATES"]["RED"], SIM_CONFIG["SIGNAL_STATES"]["ALL_RED"]):
                    must_stop = True
                elif signal_state == SIM_CONFIG["SIGNAL_STATES"]["YELLOW"]:
                    stopping_dist = (v * v) / (2.0 * b)
                    if dist_to_stop > stopping_dist * 1.1 and dist_to_stop > 25.0:
                        must_stop = True

                if self.is_emergency:
                    must_stop = False

                if must_stop:
                    delta_v = v
                    s_star = s0 + max(0.0, v * T + (v * delta_v) / (2.0 * math.sqrt(a * b)))
                    stop_gap = max(dist_to_stop, 0.5)
                    stop_decel = -a * ((s_star / stop_gap) ** 2)
                    if stop_decel < signal_term:
                        signal_term = stop_decel

        total_accel = free_road_term + interaction_term + signal_term
        return max(-SIM_CONFIG["HARD_BRAKING"], min(a, total_accel))

    def compute_world_transform(self):
        """
        Computes (x, y) and heading angle based on standard Right-Hand Traffic:
        - Road A (North): inbound on West side (x < 0), heading SOUTH (angle = +pi/2, facing down)
        - Road B (East): inbound on North side (y < 0), heading WEST (angle = pi, facing left)
        - Road C (South): inbound on East side (x > 0), heading NORTH (angle = -pi/2, facing up)
        - Road D (West): inbound on South side (y > 0), heading EAST (angle = 0, facing right)
        """
        # Lane offset from centerline:
        # Lane 0 (outer curb): 52.5px
        # Lane 1 (inner): 17.5px
        lane_offset = 52.5 if self.lane_index == 0 else 17.5
        approach_dist = self.total_approach_distance # 480px
        stop_s = self.stop_line_s                    # 405px (75px from center)

        if self.s <= stop_s:
            # Linear approach towards the stop line
            dist_from_center = approach_dist - self.s

            if self.road_id == "A":
                # Approaching from North, travelling South
                self.x = -lane_offset
                self.y = -dist_from_center
                self.angle = math.pi / 2.0  # Facing South / Down
            elif self.road_id == "B":
                # Approaching from East, travelling West
                self.x = dist_from_center
                self.y = -lane_offset
                self.angle = math.pi        # Facing West / Left
            elif self.road_id == "C":
                # Approaching from South, travelling North
                self.x = lane_offset
                self.y = dist_from_center
                self.angle = -math.pi / 2.0 # Facing North / Up
            elif self.road_id == "D":
                # Approaching from West, travelling East
                self.x = -dist_from_center
                self.y = lane_offset
                self.angle = 0.0            # Facing East / Right

        else:
            # Crossing or past the intersection stop line
            s_past = self.s - stop_s

            if self.intended_maneuver == "STRAIGHT":
                if self.road_id == "A":
                    self.x = -lane_offset
                    self.y = -75.0 + s_past
                    self.angle = math.pi / 2.0  # Keeps facing South
                elif self.road_id == "B":
                    self.x = 75.0 - s_past
                    self.y = -lane_offset
                    self.angle = math.pi        # Keeps facing West
                elif self.road_id == "C":
                    self.x = lane_offset
                    self.y = 75.0 - s_past
                    self.angle = -math.pi / 2.0 # Keeps facing North
                elif self.road_id == "D":
                    self.x = -75.0 + s_past
                    self.y = lane_offset
                    self.angle = 0.0            # Keeps facing East

            elif self.intended_maneuver == "RIGHT":
                # Smooth right turn quarter-circle curve (radius 22.5px)
                R = 22.5
                arc = (math.pi / 2.0) * R

                if s_past < arc:
                    u = s_past / arc
                    alpha = u * (math.pi / 2.0)

                    if self.road_id == "A":
                        # North turning into Westbound exit
                        self.x = -75.0 + R * math.cos(alpha)
                        self.y = -75.0 + R * math.sin(alpha)
                        self.angle = (math.pi / 2.0) + alpha # Rotates from pi/2 -> pi
                    elif self.road_id == "B":
                        # East turning into Northbound exit
                        self.x = 75.0 - R * math.sin(alpha)
                        self.y = -75.0 + R * math.cos(alpha)
                        self.angle = math.pi + alpha         # Rotates from pi -> 3pi/2 (-pi/2)
                    elif self.road_id == "C":
                        # South turning into Eastbound exit
                        self.x = 75.0 - R * math.cos(alpha)
                        self.y = 75.0 - R * math.sin(alpha)
                        self.angle = (-math.pi / 2.0) + alpha # Rotates from -pi/2 -> 0
                    elif self.road_id == "D":
                        # West turning into Southbound exit
                        self.x = -75.0 + R * math.sin(alpha)
                        self.y = 75.0 - R * math.cos(alpha)
                        self.angle = alpha                    # Rotates from 0 -> pi/2

                else:
                    # After turn completion: travelling along outgoing exit lane
                    s_exit = s_past - arc
                    if self.road_id == "A":
                        self.x = -75.0 - s_exit
                        self.y = -52.5
                        self.angle = math.pi        # Facing West
                    elif self.road_id == "B":
                        self.x = 52.5
                        self.y = -75.0 - s_exit
                        self.angle = -math.pi / 2.0 # Facing North
                    elif self.road_id == "C":
                        self.x = 75.0 + s_exit
                        self.y = 52.5
                        self.angle = 0.0            # Facing East
                    elif self.road_id == "D":
                        self.x = -52.5
                        self.y = 75.0 + s_exit
                        self.angle = math.pi / 2.0  # Facing South

            elif self.intended_maneuver == "LEFT":
                # Smooth left turn quarter-circle curve (radius 92.5px)
                R = 92.5
                arc = (math.pi / 2.0) * R

                if s_past < arc:
                    u = s_past / arc
                    alpha = u * (math.pi / 2.0)

                    if self.road_id == "A":
                        # North turning into Eastbound exit
                        self.x = 75.0 - R * math.cos(alpha)
                        self.y = -75.0 + R * math.sin(alpha)
                        self.angle = (math.pi / 2.0) - alpha # Rotates from pi/2 -> 0
                    elif self.road_id == "B":
                        # East turning into Southbound exit
                        self.x = 75.0 - R * math.sin(alpha)
                        self.y = 75.0 - R * math.cos(alpha)
                        self.angle = math.pi - alpha         # Rotates from pi -> pi/2
                    elif self.road_id == "C":
                        # South turning into Westbound exit
                        self.x = -75.0 + R * math.cos(alpha)
                        self.y = 75.0 - R * math.sin(alpha)
                        self.angle = (-math.pi / 2.0) - alpha # Rotates from -pi/2 -> -pi
                    elif self.road_id == "D":
                        # West turning into Northbound exit
                        self.x = -75.0 + R * math.sin(alpha)
                        self.y = -75.0 + R * math.cos(alpha)
                        self.angle = -alpha                  # Rotates from 0 -> -pi/2

                else:
                    # After turn completion: travelling along outgoing exit lane
                    s_exit = s_past - arc
                    if self.road_id == "A":
                        self.x = 75.0 + s_exit
                        self.y = 17.5
                        self.angle = 0.0            # Facing East
                    elif self.road_id == "B":
                        self.x = -17.5
                        self.y = 75.0 + s_exit
                        self.angle = math.pi / 2.0  # Facing South
                    elif self.road_id == "C":
                        self.x = -75.0 - s_exit
                        self.y = -17.5
                        self.angle = math.pi        # Facing West
                    elif self.road_id == "D":
                        self.x = 17.5
                        self.y = -75.0 - s_exit
                        self.angle = -math.pi / 2.0 # Facing North

            else:
                # Default straight traversal
                if self.road_id == "A":
                    self.x, self.y, self.angle = -lane_offset, -75.0 + s_past, math.pi / 2.0
                elif self.road_id == "B":
                    self.x, self.y, self.angle = 75.0 - s_past, -lane_offset, math.pi
                elif self.road_id == "C":
                    self.x, self.y, self.angle = lane_offset, 75.0 - s_past, -math.pi / 2.0
                elif self.road_id == "D":
                    self.x, self.y, self.angle = -75.0 + s_past, lane_offset, 0.0

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type_key,
            "name": self.type_spec["name"],
            "roadId": self.road_id,
            "laneIndex": self.lane_index,
            "maneuver": self.intended_maneuver,
            "color": self.color,
            "isEmergency": self.is_emergency,
            "emergencyType": self.emergency_type,
            "speed": round(self.speed, 1),
            "waitTime": round(self.wait_time, 1),
            "brakeLightsOn": self.brake_lights_on,
            "turnSignalOn": self.turn_signal_on,
            "sirenPhase": round(self.siren_phase, 2),
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "angle": round(self.angle, 3),
            "length": self.length,
            "width": self.width
        }
