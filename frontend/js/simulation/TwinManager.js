/**
 * AI Adaptive Traffic Signal Digital Twin - Twin Manager
 * Orchestrates synchronized twin simulations (Fixed vs AI Adaptive) with identical traffic stream.
 */

import { IntersectionSim } from './IntersectionSim.js';
import { TrafficGenerator } from './TrafficGenerator.js';
import { FixedTimeController } from '../controllers/FixedTimeController.js';
import { AdaptiveAIController } from '../controllers/AdaptiveAIController.js';

export class TwinManager {
  constructor() {
    // Twin instances
    this.fixedController = new FixedTimeController();
    this.aiController = new AdaptiveAIController();

    this.simFixed = new IntersectionSim('SIM_FIXED', 'Conventional Fixed-Time Signal', this.fixedController);
    this.simAdaptive = new IntersectionSim('SIM_ADAPTIVE', 'AI Adaptive Traffic Signal', this.aiController);

    // Shared Traffic Generator guarantees identical vehicle streams
    this.generator = new TrafficGenerator(42);

    // Playback state
    this.isPlaying = true;
    this.speedMultiplier = 1.0;
    this.viewMode = 'DUAL'; // 'DUAL', 'AI_ONLY', 'FIXED_ONLY'

    // Real-time delta comparison cache
    this.comparisonStats = {
      waitTimeReductionPct: 0,
      queueReductionPct: 0,
      throughputGainPct: 0,
      co2SavedKg: 0,
      fuelSavedLiters: 0
    };
  }

  /**
   * Resets both twin simulations and generator
   */
  reset() {
    this.generator = new TrafficGenerator(42);
    this.simFixed.reset();
    this.simAdaptive.reset();
    this.comparisonStats = {
      waitTimeReductionPct: 0,
      queueReductionPct: 0,
      throughputGainPct: 0,
      co2SavedKg: 0,
      fuelSavedLiters: 0
    };
  }

  /**
   * Updates both simulations in lockstep
   * @param {number} rawDt Wall clock delta time in seconds
   */
  update(rawDt) {
    if (!this.isPlaying) return;

    // Apply speed multiplier and clamp max step to prevent physics tunneling
    const dt = Math.min(0.1, rawDt * this.speedMultiplier);

    // 1. Generate new vehicles from shared generator
    const newSpecs = this.generator.update(dt, this.simAdaptive.simTime);

    // 2. Dispatch identical vehicles to BOTH twins
    for (const spec of newSpecs) {
      // Spawn on Fixed-Time twin
      this.simFixed.spawnVehicle({ ...spec });
      // Spawn on AI Adaptive twin
      this.simAdaptive.spawnVehicle({ ...spec });
    }

    // 3. Update both simulations
    this.simFixed.update(dt, this.generator.arrivalRates);
    this.simAdaptive.update(dt, this.generator.arrivalRates);

    // 4. Compute real-time comparison analytics
    this.calculateComparativeDeltas();
  }

  /**
   * Calculates comparative percentage improvements
   */
  calculateComparativeDeltas() {
    const fixedWait = this.simFixed.avgWaitTime;
    const aiWait = this.simAdaptive.avgWaitTime;

    let waitReduction = 0;
    if (fixedWait > 0.5) {
      waitReduction = Math.round(((fixedWait - aiWait) / fixedWait) * 1000) / 10;
    }

    const fixedQ = this.simFixed.currentTotalQueue;
    const aiQ = this.simAdaptive.currentTotalQueue;
    let qReduction = 0;
    if (fixedQ > 0) {
      qReduction = Math.round(((fixedQ - aiQ) / fixedQ) * 1000) / 10;
    }

    const fixedTP = this.simFixed.totalPassed;
    const aiTP = this.simAdaptive.totalPassed;
    let tpGain = 0;
    if (fixedTP > 5) {
      tpGain = Math.round(((aiTP - fixedTP) / fixedTP) * 1000) / 10;
    }

    const fuelSaved = Math.max(0, Math.round((this.simFixed.fuelWastedLiters - this.simAdaptive.fuelWastedLiters) * 100) / 100);
    const co2Saved = Math.max(0, Math.round((this.simFixed.co2EmissionsKg - this.simAdaptive.co2EmissionsKg) * 100) / 100);

    this.comparisonStats = {
      waitTimeReductionPct: waitReduction,
      queueReductionPct: qReduction,
      throughputGainPct: tpGain,
      co2SavedKg: co2Saved,
      fuelSavedLiters: fuelSaved
    };
  }

  /**
   * Manually spawns vehicle into both twins
   */
  spawnManualVehicle(roadId, typeKey = 'SEDAN') {
    const spec = this.generator.createManualVehicle(roadId, typeKey, this.simAdaptive.simTime);
    this.simFixed.spawnVehicle({ ...spec });
    this.simAdaptive.spawnVehicle({ ...spec });
  }

  /**
   * Manually spawns an emergency vehicle into both twins
   */
  spawnEmergencyVehicle(roadId = 'A') {
    const spec = this.generator.createEmergencyVehicle(roadId, this.simAdaptive.simTime);
    this.simFixed.spawnVehicle({ ...spec });
    this.simAdaptive.spawnVehicle({ ...spec });
  }

  /**
   * Advances simulation by 1 step while paused
   */
  step() {
    const stepDt = 0.05;
    const newSpecs = this.generator.update(stepDt, this.simAdaptive.simTime);
    for (const spec of newSpecs) {
      this.simFixed.spawnVehicle({ ...spec });
      this.simAdaptive.spawnVehicle({ ...spec });
    }
    this.simFixed.update(stepDt, this.generator.arrivalRates);
    this.simAdaptive.update(stepDt, this.generator.arrivalRates);
    this.calculateComparativeDeltas();
  }
}
