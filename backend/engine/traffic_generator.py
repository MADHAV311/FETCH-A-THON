"""
AI Adaptive Traffic Signal Digital Twin - Traffic Generator (Backend Service Layer)
Poisson stochastic arrivals, deterministic pseudo-random seeds, presets, and dynamic rush hour patterns.
"""

import math
import random
from .config import SIM_CONFIG

class TrafficGenerator:
    def __init__(self, seed=42):
        self.initial_seed = seed
        self.seed = seed
        self.random_enabled = True

        self.arrival_rates = {
            "A": 18.0,
            "B": 18.0,
            "C": 18.0,
            "D": 18.0
        }

        self.time_until_next_arrival = {
            r: self._sample_interval(r) for r in ["A", "B", "C", "D"]
        }

        self.current_preset_key = "BALANCED"
        self.rush_hour_phase_index = 0
        self.rush_hour_timer = 0.0
        self.total_generated = 0

    def _next_random(self):
        # Mulberry32 32-bit deterministic PRNG
        self.seed = (self.seed + 0x6d2b79f5) & 0xFFFFFFFF
        t = self.seed
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t = (t ^ (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF))) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    def _sample_interval(self, road_id):
        rate = self.arrival_rates.get(road_id, 10.0)
        if rate <= 0.0:
            return 999999.0
        lam = rate / 60.0
        u = max(0.0001, self._next_random())
        return -math.log(1.0 - u) / lam

    def apply_preset(self, preset_key):
        preset = SIM_CONFIG["PRESETS"].get(preset_key)
        if not preset:
            return

        self.current_preset_key = preset_key
        self.rush_hour_phase_index = 0
        self.rush_hour_timer = 0.0

        if preset.get("dynamic") and "phases" in preset:
            self.arrival_rates = dict(preset["phases"][0]["rates"])
        else:
            self.arrival_rates = dict(preset["rates"])

        for r in ["A", "B", "C", "D"]:
            self.time_until_next_arrival[r] = self._sample_interval(r)

    def set_rate(self, road_id, rate_per_min):
        self.arrival_rates[road_id] = max(0.0, min(120.0, float(rate_per_min)))
        self.time_until_next_arrival[road_id] = self._sample_interval(road_id)

    def update(self, dt, current_time):
        spawned_specs = []

        if self.current_preset_key == "RUSH_HOUR":
            preset = SIM_CONFIG["PRESETS"]["RUSH_HOUR"]
            self.rush_hour_timer += dt
            cur_phase = preset["phases"][self.rush_hour_phase_index]
            if self.rush_hour_timer >= cur_phase["durationSec"]:
                self.rush_hour_timer = 0.0
                self.rush_hour_phase_index = (self.rush_hour_phase_index + 1) % len(preset["phases"])
                new_phase = preset["phases"][self.rush_hour_phase_index]
                self.arrival_rates = dict(new_phase["rates"])

        if not self.random_enabled:
            return spawned_specs

        for r in ["A", "B", "C", "D"]:
            self.time_until_next_arrival[r] -= dt
            if self.time_until_next_arrival[r] <= 0:
                spec = self.generate_vehicle_spec(r, current_time)
                spawned_specs.append(spec)
                self.time_until_next_arrival[r] = self._sample_interval(r)

        return spawned_specs

    def generate_vehicle_spec(self, road_id, current_time, forced_type=None, forced_lane=None):
        self.total_generated += 1

        type_key = forced_type
        if not type_key:
            roll = self._next_random()
            accum = 0.0
            for key, t_spec in SIM_CONFIG["VEHICLE_TYPES"].items():
                accum += t_spec["weight"]
                if roll <= accum:
                    type_key = key
                    break
            if not type_key:
                type_key = "SEDAN"

        type_spec = SIM_CONFIG["VEHICLE_TYPES"].get(type_key, SIM_CONFIG["VEHICLE_TYPES"]["SEDAN"])
        if type_spec.get("isEmergency"):
            lane_index = forced_lane if forced_lane is not None else 1
            maneuver = "STRAIGHT"
        else:
            lane_index = forced_lane if forced_lane is not None else (0 if self._next_random() > 0.5 else 1)
            maneuver = "STRAIGHT"
            maneuver_roll = self._next_random()
            if lane_index == 0 and maneuver_roll < 0.25:
                maneuver = "RIGHT"
            elif lane_index == 1 and maneuver_roll < 0.30:
                maneuver = "LEFT"

        colors = type_spec["colors"]
        color_idx = int(self._next_random() * len(colors)) % len(colors)

        return {
            "id": f"V-{self.total_generated}",
            "type_key": type_key,
            "road_id": road_id,
            "lane_index": lane_index,
            "intended_maneuver": maneuver,
            "initial_speed": type_spec["maxSpeed"] * (0.7 + self._next_random() * 0.25),
            "color": colors[color_idx],
            "spawn_time": current_time,
            "s": 0.0
        }
