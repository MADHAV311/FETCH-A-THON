"""
AI Adaptive Traffic Signal Digital Twin - Experiment Engine (Backend Service Layer)
Executes automated comparative simulation benchmarks across traffic scenarios and compiles statistical reports.
"""

from .intersection_sim import IntersectionSim
from .traffic_generator import TrafficGenerator
from .controllers import FixedTimeController, AdaptiveAIController
from .config import SIM_CONFIG

class ExperimentEngine:
    def __init__(self):
        self.last_results = None

    def run_benchmark(self, duration_sec=120.0, step_dt=0.1):
        """
        Runs automated fast-forward headless simulation experiments comparing
        Fixed-Time vs AI Adaptive across all core presets.
        """
        scenarios = ["BALANCED", "LOW", "HEAVY", "UNEVEN", "RUSH_HOUR"]
        results = []

        for scen_key in scenarios:
            preset = SIM_CONFIG["PRESETS"][scen_key]
            
            # Setup independent twin instances for headless testing
            fixed_ctrl = FixedTimeController()
            ai_ctrl = AdaptiveAIController()
            sim_fixed = IntersectionSim(f"EXP_FIXED_{scen_key}", "Fixed", fixed_ctrl)
            sim_ai = IntersectionSim(f"EXP_AI_{scen_key}", "AI Adaptive", ai_ctrl)

            gen = TrafficGenerator(seed=100)
            gen.apply_preset(scen_key)

            # Run headless simulation loop
            t = 0.0
            while t < duration_sec:
                specs = gen.update(step_dt, t)
                for spec in specs:
                    sim_fixed.spawn_vehicle(dict(spec))
                    sim_ai.spawn_vehicle(dict(spec))

                sim_fixed.update(step_dt, gen.arrival_rates)
                sim_ai.update(step_dt, gen.arrival_rates)
                t += step_dt

            # Collect metrics
            f_wait = sim_fixed.avg_wait_time
            a_wait = sim_ai.avg_wait_time
            wait_reduction = round(((f_wait - a_wait) / f_wait * 100.0), 1) if f_wait > 0.1 else 0.0

            f_tp = sim_fixed.total_passed
            a_tp = sim_ai.total_passed
            tp_gain = round(((a_tp - f_tp) / f_tp * 100.0), 1) if f_tp > 0 else 0.0

            f_q = sim_fixed.peak_queue_observed
            a_q = sim_ai.peak_queue_observed
            q_reduction = round(((f_q - a_q) / f_q * 100.0), 1) if f_q > 0 else 0.0

            fuel_saved = max(0.0, round(sim_fixed.fuel_wasted_liters - sim_ai.fuel_wasted_liters, 2))
            co2_saved = max(0.0, round(sim_fixed.co2_emissions_kg - sim_ai.co2_emissions_kg, 2))

            results.append({
                "scenario": scen_key,
                "name": preset["name"],
                "description": preset["description"],
                "simDurationSec": duration_sec,
                "fixed": {
                    "avgWaitTime": f_wait,
                    "maxWaitTime": sim_fixed.max_wait_time_observed,
                    "totalPassed": f_tp,
                    "peakQueue": f_q,
                    "fuelWasted": sim_fixed.fuel_wasted_liters,
                    "co2Emissions": sim_fixed.co2_emissions_kg
                },
                "adaptive": {
                    "avgWaitTime": a_wait,
                    "maxWaitTime": sim_ai.max_wait_time_observed,
                    "totalPassed": a_tp,
                    "peakQueue": a_q,
                    "fuelWasted": sim_ai.fuel_wasted_liters,
                    "co2Emissions": sim_ai.co2_emissions_kg
                },
                "impact": {
                    "waitTimeReductionPct": wait_reduction,
                    "throughputGainPct": tp_gain,
                    "queueReductionPct": q_reduction,
                    "fuelSavedLiters": fuel_saved,
                    "co2SavedKg": co2_saved
                }
            })

        self.last_results = {
            "timestamp": round(duration_sec),
            "scenariosTested": len(scenarios),
            "results": results
        }
        return self.last_results
