"""
AI Adaptive Traffic Signal Digital Twin - Road Model (Backend Service Layer)
Tracks lanes, queue lengths, max waiting time, inductive loop occupancy, and signal states.
"""

from .config import SIM_CONFIG

class Road:
    def __init__(self, road_id, name, direction):
        self.id = road_id
        self.name = name
        self.direction = direction

        self.signal_state = SIM_CONFIG["SIGNAL_STATES"]["RED"]
        self.allocated_duration = 0.0
        self.elapsed_in_phase = 0.0
        self.remaining_in_phase = 0.0

        # Inbound lanes: 2 lanes
        self.lanes = [[], []]

        # Telemetry
        self.waiting_vehicles_count = 0
        self.queue_length_meters = 0
        self.max_wait_time_sec = 0.0
        self.total_wait_time_sec = 0.0
        self.total_vehicles_passed = 0
        self.cumulative_wait_time = 0.0
        self.avg_wait_time_sec = 0.0
        self.sensor_active = False
        self.priority_score = 0.0
        self.time_since_last_green = 0.0

    def reset(self):
        self.signal_state = SIM_CONFIG["SIGNAL_STATES"]["RED"]
        self.allocated_duration = 0.0
        self.elapsed_in_phase = 0.0
        self.remaining_in_phase = 0.0
        self.lanes = [[], []]
        self.waiting_vehicles_count = 0
        self.queue_length_meters = 0
        self.max_wait_time_sec = 0.0
        self.total_wait_time_sec = 0.0
        self.total_vehicles_passed = 0
        self.cumulative_wait_time = 0.0
        self.avg_wait_time_sec = 0.0
        self.sensor_active = False
        self.priority_score = 0.0
        self.time_since_last_green = 0.0

    def update_telemetry(self, dt):
        if self.signal_state != SIM_CONFIG["SIGNAL_STATES"]["GREEN"]:
            self.time_since_last_green += dt
        else:
            self.time_since_last_green = 0.0

        waiting_count = 0
        max_wait = 0.0
        sum_wait = 0.0
        loop_detected = False

        stop_s = SIM_CONFIG["SPAWN_OFFSET"] - SIM_CONFIG["STOP_LINE_OFFSET"]
        sensor_start = SIM_CONFIG["SPAWN_OFFSET"] - SIM_CONFIG["SENSOR_LOOP_OFFSET"]
        sensor_end = sensor_start + SIM_CONFIG["SENSOR_LOOP_LENGTH"]

        for lane in self.lanes:
            for v in lane:
                # Sensor loop check
                if v.s >= sensor_start - v.length and v.s <= sensorEnd if 'sensorEnd' in locals() else (v.s >= sensor_start - v.length and v.s <= sensor_end):
                    loop_detected = True

                # Queue check: stopped or slow before stop line
                if not v.has_crossed_stop_line and v.s <= stop_s + 5.0 and v.speed < 5.0:
                    waiting_count += 1
                    sum_wait += v.wait_time
                    if v.wait_time > max_wait:
                        max_wait = v.wait_time

        self.waiting_vehicles_count = waiting_count
        self.queue_length_meters = int(waiting_count * 7.5)
        self.max_wait_time_sec = round(max_wait, 1)
        self.total_wait_time_sec = round(sum_wait, 1)
        self.sensor_active = loop_detected

        if self.total_vehicles_passed > 0:
            self.avg_wait_time_sec = round(self.cumulative_wait_time / self.total_vehicles_passed, 1)

    def on_vehicle_passed(self, vehicle):
        self.total_vehicles_passed += 1
        self.cumulative_wait_time += vehicle.wait_time

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "direction": self.direction,
            "signalState": self.signal_state,
            "allocatedDuration": round(self.allocated_duration, 1),
            "remainingInPhase": round(self.remaining_in_phase, 1),
            "waitingVehicles": self.waiting_vehicles_count,
            "queueLengthMeters": self.queue_length_meters,
            "maxWaitTime": self.max_wait_time_sec,
            "avgWaitTime": self.avg_wait_time_sec,
            "totalPassed": self.total_vehicles_passed,
            "sensorActive": self.sensor_active,
            "priorityScore": self.priority_score,
            "timeSinceLastGreen": round(self.time_since_last_green, 1)
        }
