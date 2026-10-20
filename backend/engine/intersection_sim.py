"""
AI Adaptive Traffic Signal Digital Twin - Intersection Simulation Instance (Backend Service Layer)
Manages vehicles, roads, signal controller execution, metrics aggregation, directional pole sirens,
pedestrian crossing VRU engine, and telemetry history.
"""

from .config import SIM_CONFIG
from .road import Road
from .vehicle import Vehicle
from .pedestrian import PedestrianCrossingManager

class IntersectionSim:
    def __init__(self, sim_id, name, controller):
        self.id = sim_id
        self.name = name
        self.controller = controller

        self.roads = {
            "A": Road("A", SIM_CONFIG["ROADS"]["NORTH"]["name"], "N"),
            "B": Road("B", SIM_CONFIG["ROADS"]["EAST"]["name"],  "E"),
            "C": Road("C", SIM_CONFIG["ROADS"]["SOUTH"]["name"], "S"),
            "D": Road("D", SIM_CONFIG["ROADS"]["WEST"]["name"],  "W")
        }

        self.vehicles = []

        # Pedestrian VRU Crossing Engine
        self.pedestrian_manager = PedestrianCrossingManager()

        # Active Accident Incident Obstacle
        self.active_accident = None
        self.active_crime = None

        # Directional Pole-Mounted Visual/Acoustic Sirens
        self.directional_sirens = {
            "A": {"id": "POLE_NORTH", "roadId": "A", "name": "North Signal Pole (Road A)", "active": False, "type": None, "strobe": False, "decibels": 0, "sirenPhase": 0.0},
            "B": {"id": "POLE_EAST",  "roadId": "B", "name": "East Signal Pole (Road B)",  "active": False, "type": None, "strobe": False, "decibels": 0, "sirenPhase": 0.0},
            "C": {"id": "POLE_SOUTH", "roadId": "C", "name": "South Signal Pole (Road C)", "active": False, "type": None, "strobe": False, "decibels": 0, "sirenPhase": 0.0},
            "D": {"id": "POLE_WEST",  "roadId": "D", "name": "West Signal Pole (Road D)",  "active": False, "type": None, "strobe": False, "decibels": 0, "sirenPhase": 0.0}
        }

        self.sim_time = 0.0
        self.total_spawned = 0
        self.total_passed = 0
        self.total_exited = 0

        self.total_wait_time = 0.0
        self.avg_wait_time = 0.0
        self.max_wait_time_observed = 0.0
        self.current_total_queue = 0
        self.peak_queue_observed = 0
        self.total_queue_meters = 0

        self.throughput_per_min = 0.0
        self.fuel_wasted_liters = 0.0
        self.co2_emissions_kg = 0.0

        self.history = {
            "time": [],
            "avgWaitTime": [],
            "queueLength": [],
            "throughput": [],
            "cumulativeCleared": []
        }
        self.history_sample_timer = 0.0
        self.history_sample_interval = 1.0

    def reset(self):
        self.sim_time = 0.0
        self.total_spawned = 0
        self.total_passed = 0
        self.total_exited = 0
        self.total_wait_time = 0.0
        self.avg_wait_time = 0.0
        self.max_wait_time_observed = 0.0
        self.current_total_queue = 0
        self.peak_queue_observed = 0
        self.total_queue_meters = 0
        self.throughput_per_min = 0.0
        self.fuel_wasted_liters = 0.0
        self.co2_emissions_kg = 0.0

        for road in self.roads.values():
            road.reset()
        self.vehicles = []
        self.controller.reset()
        self.active_accident = None
        self.pedestrian_manager = PedestrianCrossingManager()

        for pole in self.directional_sirens.values():
            pole["active"] = False
            pole["type"] = None
            pole["strobe"] = False
            pole["decibels"] = 0
            pole["sirenPhase"] = 0.0

        self.history = {
            "time": [],
            "avgWaitTime": [],
            "queueLength": [],
            "throughput": [],
            "cumulativeCleared": []
        }
        self.history_sample_timer = 0.0

    def spawn_vehicle(self, spec):
        road = self.roads.get(spec["road_id"])
        if not road:
            return None

        is_em = bool(spec.get("is_emergency") or spec.get("type_key") in ["AMBULANCE", "FIRE_ENGINE", "EMERGENCY"])
        lane_idx = spec["lane_index"]
        lane = road.lanes[lane_idx]

        for lead in lane:
            if lead.s < 45.0:
                if is_em:
                    # Emergency vehicle has absolute priority: advance blocking vehicle forward
                    lead.s = max(lead.s + 50.0, 50.0)
                    lead.compute_world_transform()
                else:
                    # Regular spawn space blocked
                    return None

        v = Vehicle({**spec, "spawn_time": self.sim_time})
        lane.append(v)
        self.vehicles.append(v)
        self.total_spawned += 1
        return v

    def update(self, dt, arrival_rates=None):
        self.sim_time += dt

        # 1. Update Directional Pole Sirens based on inbound emergency vehicles
        for road_id, pole in self.directional_sirens.items():
            road = self.roads.get(road_id)
            emergency_veh = None
            if road:
                for lane in road.lanes:
                    for v in lane:
                        if v.is_emergency and not v.has_crossed_stop_line:
                            emergency_veh = v
                            break
                    if emergency_veh:
                        break
            if emergency_veh:
                pole["active"] = True
                pole["type"] = emergency_veh.emergency_type or "AMBULANCE"
                pole["strobe"] = True
                pole["decibels"] = 115
                pole["sirenPhase"] = emergency_veh.siren_phase
            else:
                pole["active"] = False
                pole["type"] = None
                pole["strobe"] = False
                pole["decibels"] = 0
                pole["sirenPhase"] = 0.0

        # Activate pole sirens for severe accident
        if self.active_accident and self.active_accident.get("callEmergency"):
            acc_road = self.active_accident.get("roadId", "C")
            if acc_road in self.directional_sirens:
                p = self.directional_sirens[acc_road]
                p["active"] = True
                p["type"] = "ACCIDENT"
                p["strobe"] = True
                p["decibels"] = 115
                p["sirenPhase"] = (self.sim_time * 2.5) % 1.0

        # Activate pole sirens for critical crime scene (Blue & Red Police Warning Strobe)
        if self.active_crime and self.active_crime.get("callPolice"):
            crm_road = self.active_crime.get("roadId", "B")
            if crm_road in self.directional_sirens:
                p = self.directional_sirens[crm_road]
                p["active"] = True
                p["type"] = "POLICE"
                p["strobe"] = True
                p["decibels"] = 110
                p["sirenPhase"] = (self.sim_time * 3.0) % 1.0

        # 2. Update Pedestrian Crossing Manager
        self.pedestrian_manager.update(dt)

        # 3. Update Controller
        if hasattr(self.controller, 'update'):
            if self.controller.type == "ADAPTIVE":
                self.controller.update(dt, self.roads, arrival_rates)
            else:
                self.controller.update(dt, self.roads)

        # If pedestrian scramble active, hold all vehicle signals at ALL_RED
        if self.pedestrian_manager.scramble_active:
            for road in self.roads.values():
                road.signal_state = SIM_CONFIG["SIGNAL_STATES"]["ALL_RED"]
                road.remaining_in_phase = max(0.0, self.pedestrian_manager.scramble_timer)

        # If severe accident is active and this is AI adaptive controller, enforce perimeter lockdown
        if self.active_accident and getattr(self.controller, 'type', '') == "ADAPTIVE":
            acc_road = self.active_accident.get("roadId")
            if self.active_accident.get("trafficAction") == "PERIMETER_LOCKDOWN_UPSTREAM_RED_DOWNSTREAM_GREEN":
                if acc_road in self.roads:
                    self.roads[acc_road].signal_state = SIM_CONFIG["SIGNAL_STATES"]["RED"]

        # 4. Update Vehicles in Each Lane
        for road in self.roads.values():
            signal_state = road.signal_state

            for lane in road.lanes:
                lane.sort(key=lambda veh: veh.s, reverse=True)

                for i, v in enumerate(lane):
                    lead_veh = lane[i - 1] if i > 0 else None
                    prev_crossed = v.has_crossed_stop_line

                    v.update(dt, lead_veh, signal_state, self.sim_time)

                    if not prev_crossed and v.has_crossed_stop_line:
                        self.total_passed += 1
                        self.total_wait_time += v.wait_time
                        road.on_vehicle_passed(v)
                        if v.wait_time > self.max_wait_time_observed:
                            self.max_wait_time_observed = v.wait_time

            road.update_telemetry(dt)

        # 5. Clean up Exited Vehicles
        surviving = []
        for v in self.vehicles:
            if v.has_exited:
                self.total_exited += 1
                road = self.roads.get(v.road_id)
                if road:
                    lane = road.lanes[v.lane_index]
                    if v in lane:
                        lane.remove(v)
            else:
                surviving.append(v)
        self.vehicles = surviving

        # 6. Aggregate Global Metrics
        q_count = sum(r.waiting_vehicles_count for r in self.roads.values())
        q_meters = sum(r.queue_length_meters for r in self.roads.values())
        self.current_total_queue = q_count
        self.total_queue_meters = q_meters
        if q_count > self.peak_queue_observed:
            self.peak_queue_observed = q_count

        if self.total_passed > 0:
            self.avg_wait_time = round(self.total_wait_time / self.total_passed, 1)

        if self.sim_time > 5.0:
            self.throughput_per_min = round(self.total_passed / (self.sim_time / 60.0), 1)

        idle_hours = (self.total_wait_time + (q_count * dt)) / 3600.0
        self.fuel_wasted_liters = round(idle_hours * SIM_CONFIG["ENVIRONMENTAL"]["IDLE_FUEL_LITER_PER_HOUR"], 2)
        self.co2_emissions_kg = round(self.fuel_wasted_liters * SIM_CONFIG["ENVIRONMENTAL"]["IDLE_CO2_KG_PER_LITER"], 2)

        # 7. History Sampling
        self.history_sample_timer += dt
        if self.history_sample_timer >= self.history_sample_interval:
            self.history_sample_timer = 0.0
            self._sample_history()

    def _sample_history(self):
        self.history["time"].append(round(self.sim_time))
        self.history["avgWaitTime"].append(self.avg_wait_time)
        self.history["queueLength"].append(self.current_total_queue)
        self.history["throughput"].append(self.throughput_per_min)
        self.history["cumulativeCleared"].append(self.total_passed)

        if len(self.history["time"]) > 120:
            for k in self.history:
                self.history[k].pop(0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "simTime": round(self.sim_time, 1),
            "totalSpawned": self.total_spawned,
            "totalPassed": self.total_passed,
            "totalExited": self.total_exited,
            "avgWaitTime": self.avg_wait_time,
            "maxWaitTime": round(self.max_wait_time_observed, 1),
            "currentQueue": self.current_total_queue,
            "peakQueue": self.peak_queue_observed,
            "queueMeters": self.total_queue_meters,
            "throughput": self.throughput_per_min,
            "fuelWasted": self.fuel_wasted_liters,
            "co2Emissions": self.co2_emissions_kg,
            "roads": {r_id: r.to_dict() for r_id, r in self.roads.items()},
            "vehicles": [v.to_dict() for v in self.vehicles],
            "controller": self.controller.to_dict(),
            "directionalSirens": self.directional_sirens,
            "pedestrians": self.pedestrian_manager.to_dict(),
            "scrambleActive": self.pedestrian_manager.scramble_active,
            "activeAccident": self.active_accident,
            "activeCrime": self.active_crime,
            "history": self.history
        }
