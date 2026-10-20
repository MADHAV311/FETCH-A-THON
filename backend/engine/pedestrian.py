"""
AI Adaptive Traffic Signal Digital Twin - Pedestrian & VRU Crossing Engine
Manages crosswalk waiting queues, pedestrian push buttons, AI crowd density detection,
and All-Pedestrian Scramble Phase (Barnes Dance) activation.
"""

import math
import random
from .config import SIM_CONFIG

class PedestrianCrossingManager:
    def __init__(self):
        cfg = SIM_CONFIG["PEDESTRIAN_CONFIG"]
        self.crosswalk_offset = cfg["CROSSWALK_OFFSET"]
        self.walk_speed = cfg["WALK_SPEED"]
        self.scramble_duration = cfg["SCRAMBLE_DURATION"]
        self.min_crowd_for_scramble = cfg["MIN_CROWD_FOR_SCRAMBLE"]

        # Pedestrian waiting groups on each corner/road
        # A: North, B: East, C: South, D: West
        self.waiting_counts = {"A": 2, "B": 1, "C": 3, "D": 1}
        self.pedestrians = [] # Active walking pedestrians
        self.ped_id_counter = 1

        self.demand_button_pressed = False
        self.scramble_active = False
        self.scramble_timer = 0.0

        # Smart School Zone Computer Vision Tracking
        self.school_config = SIM_CONFIG.get("SCHOOL_ZONE_CONFIG", {})
        self.school_zone_active = False
        self.school_scenario = None # "SMALL_GROUP" or "PLATOON_INFLOW"
        self.curb_waiting_students = 0
        self.trailing_inflow_students = 0
        self.aggregation_timer = 0.0 # Time remaining before activating vehicle red
        self.cv_confidence = 0.0
        self.cv_decision = ""
        self.crossing_window = 0.0

        # Pre-seed initial waiting pedestrians
        self._spawn_initial_pedestrians()

    def _spawn_initial_pedestrians(self):
        self.pedestrians = []
        for road_id, count in self.waiting_counts.items():
            for i in range(count):
                self._add_waiting_pedestrian(road_id)

    def _add_waiting_pedestrian(self, road_id):
        self.ped_id_counter += 1
        rw = SIM_CONFIG["ROAD_WIDTH"] / 2
        offset = self.crosswalk_offset

        # Define crosswalk endpoints for roads A, B, C, D
        if road_id == "A": # North crosswalk (horizontal crossing)
            start_x = -rw - 12 + random.uniform(-4, 4)
            start_y = -offset + random.uniform(-6, 6)
            target_x = rw + 12
            target_y = start_y
        elif road_id == "B": # East crosswalk (vertical crossing)
            start_x = offset + random.uniform(-6, 6)
            start_y = -rw - 12 + random.uniform(-4, 4)
            target_x = start_x
            target_y = rw + 12
        elif road_id == "C": # South crosswalk (horizontal crossing)
            start_x = -rw - 12 + random.uniform(-4, 4)
            start_y = offset + random.uniform(-6, 6)
            target_x = rw + 12
            target_y = start_y
        else: # West crosswalk (vertical crossing)
            start_x = -offset + random.uniform(-6, 6)
            start_y = -rw - 12 + random.uniform(-4, 4)
            target_x = start_x
            target_y = rw + 12

        self.pedestrians.append({
            "id": f"PED-{self.ped_id_counter}",
            "roadId": road_id,
            "x": start_x,
            "y": start_y,
            "startX": start_x,
            "startY": start_y,
            "targetX": target_x,
            "targetY": target_y,
            "state": "WAITING", # "WAITING", "CROSSING", "CLEARED"
            "progress": 0.0,
            "speed": self.walk_speed * random.uniform(0.9, 1.2),
            "walkPhase": random.uniform(0, math.pi * 2)
        })

    def press_demand_button(self, road_id="A"):
        """Pedestrian demand push button pressed."""
        self.demand_button_pressed = True
        self.waiting_counts[road_id] = self.waiting_counts.get(road_id, 0) + 2
        self._add_waiting_pedestrian(road_id)
        self._add_waiting_pedestrian(road_id)

    def trigger_crowd_surge(self):
        """Simulate a pedestrian crowd surge at crosswalks."""
        self.demand_button_pressed = True
        for r in ["A", "B", "C", "D"]:
            self.waiting_counts[r] = self.waiting_counts.get(r, 0) + 3
            for _ in range(3):
                self._add_waiting_pedestrian(r)

    def trigger_school_zone(self, scenario="SMALL_GROUP"):
        """
        Triggers School Zone Computer Vision dynamic crossing logic:
        - SMALL_GROUP: e.g. 2 students waiting, 0 trailing inflow -> Immediate Red signal for cars, quick 8s walk
        - PLATOON_INFLOW: e.g. 10 students waiting + 6 approaching behind -> Hold car green for 4s aggregation window, then 18s consolidated scramble
        """
        self.school_zone_active = True
        self.school_scenario = scenario

        # Clear existing Road A pedestrians to accurately reflect scenario count
        self.pedestrians = [p for p in self.pedestrians if p["roadId"] != "A"]

        if scenario == "SMALL_GROUP":
            self.curb_waiting_students = 2
            self.trailing_inflow_students = 0
            self.cv_confidence = 97.4
            self.aggregation_timer = 0.0
            self.crossing_window = 8.0
            self.cv_decision = (
                "ISOLATED SMALL GROUP: 2 students detected at curb, 0 trailing inflow. "
                "Signal immediately turns RED for vehicles with quick 8.0s crossing window."
            )
            self.waiting_counts["A"] = 2
            for _ in range(2):
                self._add_waiting_pedestrian("A")

            # Immediate phase switch: cars get RED, 8s walk window
            self.scramble_duration = 8.0
            self.activate_scramble()

        else: # PLATOON_INFLOW
            self.curb_waiting_students = 10
            self.trailing_inflow_students = 6
            self.cv_confidence = 98.2
            self.aggregation_timer = 4.0
            self.crossing_window = 18.0
            self.cv_decision = (
                "STUDENT PLATOON + TRAILING INFLOW: 10 students at curb + 6 approaching behind. "
                "Holding vehicle green for 4s aggregation window, then activating consolidated Barnes Dance Scramble (18.0s)."
            )
            self.waiting_counts["A"] = 16
            for _ in range(16):
                self._add_waiting_pedestrian("A")
            # Scramble will activate automatically after aggregation_timer elapses!

    def clear_school_zone(self):
        self.school_zone_active = False
        self.school_scenario = None
        self.aggregation_timer = 0.0
        self.curb_waiting_students = 0
        self.trailing_inflow_students = 0

    def should_trigger_scramble(self):
        """Checks if pedestrian conditions warrant a scramble phase."""
        total_waiting = sum(self.waiting_counts.values())
        return self.demand_button_pressed or (total_waiting >= self.min_crowd_for_scramble)

    def activate_scramble(self):
        """Starts the All-Pedestrian Scramble Phase."""
        self.scramble_active = True
        self.scramble_timer = self.scramble_duration
        self.demand_button_pressed = False

        # Transition waiting pedestrians to CROSSING
        for p in self.pedestrians:
            if p["state"] == "WAITING":
                p["state"] = "CROSSING"

    def update(self, dt, current_signal_state="RED"):
        # Handle School Zone Inflow Aggregation Countdown
        if self.school_zone_active and self.aggregation_timer > 0:
            self.aggregation_timer -= dt
            if self.aggregation_timer <= 0:
                self.aggregation_timer = 0.0
                self.curb_waiting_students += self.trailing_inflow_students
                self.trailing_inflow_students = 0
                self.cv_decision = (
                    f"AGGREGATION COMPLETE: All {self.curb_waiting_students} students assembled at crosswalk. "
                    f"Vehicle signals turning ALL-RED. Consolidated Barnes Dance Scramble active (18.0s)!"
                )
                self.scramble_duration = 18.0
                self.activate_scramble()

        if self.scramble_active:
            self.scramble_timer -= dt
            if self.scramble_timer <= 0:
                self.scramble_active = False
                self.scramble_timer = 0.0
                # Reset waiting counts after clearance
                self.waiting_counts = {"A": 1, "B": 1, "C": 1, "D": 1}
                self.pedestrians = [p for p in self.pedestrians if p["state"] != "CLEARED"]
                # Add new casual arrivals
                for r in ["A", "B", "C", "D"]:
                    if len([p for p in self.pedestrians if p["roadId"] == r and p["state"] == "WAITING"]) < 1:
                        self._add_waiting_pedestrian(r)

        # Update walking pedestrians
        for p in self.pedestrians:
            if p["state"] == "CROSSING":
                dx = p["targetX"] - p["startX"]
                dy = p["targetY"] - p["startY"]
                dist = math.hypot(dx, dy)
                if dist > 0:
                    step = (p["speed"] * dt) / dist
                    p["progress"] += step
                    p["x"] = p["startX"] + dx * min(1.0, p["progress"])
                    p["y"] = p["startY"] + dy * min(1.0, p["progress"])
                    p["walkPhase"] = (p["walkPhase"] + dt * 10.0) % (math.pi * 2)

                    if p["progress"] >= 1.0:
                        p["state"] = "CLEARED"

    def to_dict(self):
        total_waiting = sum(len([p for p in self.pedestrians if p["roadId"] == r and p["state"] == "WAITING"]) for r in ["A", "B", "C", "D"])
        total_crossing = len([p for p in self.pedestrians if p["state"] == "CROSSING"])

        return {
            "scrambleActive": self.scramble_active,
            "scrambleTimer": round(self.scramble_timer, 1),
            "demandButtonPressed": self.demand_button_pressed,
            "totalWaiting": total_waiting,
            "totalCrossing": total_crossing,
            "schoolZone": {
                "active": self.school_zone_active,
                "scenario": self.school_scenario,
                "curbWaiting": self.curb_waiting_students,
                "trailingInflow": self.trailing_inflow_students,
                "aggregationTimer": round(self.aggregation_timer, 1),
                "cvConfidence": self.cv_confidence,
                "cvDecision": self.cv_decision,
                "crossingWindow": round(self.crossing_window, 1)
            },
            "pedestrians": self.pedestrians[:30] # list of active pedestrians for canvas rendering
        }
