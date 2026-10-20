/**
 * AI Adaptive Traffic Signal Digital Twin - Traffic Generation Engine
 * Handles Poisson arrivals, preset patterns, dynamic rush-hour flow, and synchronized twin spawning.
 */

import { SIM_CONFIG } from '../config.js';
import { Vehicle } from '../models/Vehicle.js';

export class TrafficGenerator {
  constructor(seed = 12345) {
    this.initialSeed = seed;
    this.seed = seed;
    this.randomEnabled = true;

    // Rates in vehicles per minute for Road A, B, C, D
    this.arrivalRates = {
      A: 18,
      B: 18,
      C: 18,
      D: 18
    };

    // Poisson arrival timers (seconds until next arrival)
    this.timeUntilNextArrival = {
      A: this.sampleInterarrivalTime('A'),
      B: this.sampleInterarrivalTime('B'),
      C: this.sampleInterarrivalTime('C'),
      D: this.sampleInterarrivalTime('D')
    };

    // Active preset
    this.currentPresetKey = 'BALANCED';
    this.rushHourPhaseIndex = 0;
    this.rushHourTimer = 0;

    // Vehicle counter
    this.totalVehiclesGenerated = 0;
  }

  /**
   * Deterministic pseudo-random number generator (Mulberry32)
   */
  nextRandom() {
    let t = (this.seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  /**
   * Samples next arrival interval using exponential distribution (Poisson process)
   */
  sampleInterarrivalTime(roadId) {
    const ratePerMin = this.arrivalRates[roadId] || 10;
    if (ratePerMin <= 0) return 999999;
    
    const lambda = ratePerMin / 60.0; // Vehicles per second
    const u = Math.max(0.0001, this.nextRandom());
    return -Math.log(1 - u) / lambda;
  }

  /**
   * Sets a predefined traffic preset
   */
  applyPreset(presetKey) {
    const preset = SIM_CONFIG.PRESETS[presetKey];
    if (!preset) return;

    this.currentPresetKey = presetKey;
    this.rushHourPhaseIndex = 0;
    this.rushHourTimer = 0;

    if (preset.dynamic && preset.phases) {
      // Rush hour mode: load first phase
      const phase = preset.phases[0];
      this.arrivalRates = { ...phase.rates };
    } else {
      this.arrivalRates = { ...preset.rates };
    }

    // Resample timers
    for (const rId of ['A', 'B', 'C', 'D']) {
      this.timeUntilNextArrival[rId] = this.sampleInterarrivalTime(rId);
    }
  }

  /**
   * Manually sets arrival rate for a road
   */
  setRate(roadId, ratePerMin) {
    this.arrivalRates[roadId] = Math.max(0, Math.min(120, ratePerMin));
    this.timeUntilNextArrival[roadId] = this.sampleInterarrivalTime(roadId);
  }

  /**
   * Updates generator timers and returns list of newly spawned vehicle specs
   */
  update(dt, currentTime) {
    const spawnedSpecs = [];

    // Handle dynamic Rush Hour transitions
    if (this.currentPresetKey === 'RUSH_HOUR') {
      const preset = SIM_CONFIG.PRESETS.RUSH_HOUR;
      this.rushHourTimer += dt;
      const currentPhase = preset.phases[this.rushHourPhaseIndex];

      if (this.rushHourTimer >= currentPhase.durationSec) {
        this.rushHourTimer = 0;
        this.rushHourPhaseIndex = (this.rushHourPhaseIndex + 1) % preset.phases.length;
        const newPhase = preset.phases[this.rushHourPhaseIndex];
        this.arrivalRates = { ...newPhase.rates };
      }
    }

    if (!this.randomEnabled) return spawnedSpecs;

    // Check arrivals for each road
    for (const rId of ['A', 'B', 'C', 'D']) {
      this.timeUntilNextArrival[rId] -= dt;

      if (this.timeUntilNextArrival[rId] <= 0) {
        // Generate vehicle spec
        const spec = this.generateVehicleSpec(rId, currentTime);
        spawnedSpecs.push(spec);

        // Schedule next arrival
        this.timeUntilNextArrival[rId] = this.sampleInterarrivalTime(rId);
      }
    }

    return spawnedSpecs;
  }

  /**
   * Generates vehicle blueprint
   */
  generateVehicleSpec(roadId, currentTime, forcedTypeKey = null, forcedLane = null) {
    this.totalVehiclesGenerated++;
    
    // Choose vehicle type based on weighted distribution
    let typeKey = forcedTypeKey;
    if (!typeKey) {
      const roll = this.nextRandom();
      let accum = 0;
      for (const [key, tSpec] of Object.entries(SIM_CONFIG.VEHICLE_TYPES)) {
        accum += tSpec.weight;
        if (roll <= accum) {
          typeKey = key;
          break;
        }
      }
      if (!typeKey) typeKey = 'SEDAN';
    }

    const typeSpec = SIM_CONFIG.VEHICLE_TYPES[typeKey] || SIM_CONFIG.VEHICLE_TYPES.SEDAN;

    // Lane selection (0: outer lane, 1: inner lane)
    let laneIndex = forcedLane !== null ? forcedLane : (this.nextRandom() > 0.5 ? 0 : 1);

    // Intended maneuver:
    // Outer lane (0): 75% Straight, 25% Right turn
    // Inner lane (1): 70% Straight, 30% Left turn
    let maneuver = 'STRAIGHT';
    const maneuverRoll = this.nextRandom();
    if (laneIndex === 0 && maneuverRoll < 0.25) {
      maneuver = 'RIGHT';
    } else if (laneIndex === 1 && maneuverRoll < 0.30) {
      maneuver = 'LEFT';
    }

    return {
      id: `V-${this.totalVehiclesGenerated}`,
      typeSpec,
      roadId,
      laneIndex,
      intendedManeuver: maneuver,
      initialSpeed: typeSpec.maxSpeed * (0.7 + this.nextRandom() * 0.25),
      spawnTime: currentTime,
      s: 0
    };
  }

  /**
   * Spawns a manual vehicle immediately
   */
  createManualVehicle(roadId, typeKey = 'SEDAN', currentTime = 0) {
    return this.generateVehicleSpec(roadId, currentTime, typeKey);
  }

  /**
   * Spawns an emergency ambulance
   */
  createEmergencyVehicle(roadId, currentTime = 0) {
    return this.generateVehicleSpec(roadId, currentTime, 'EMERGENCY', 1);
  }
}
