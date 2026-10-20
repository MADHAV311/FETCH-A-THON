/**
 * AI Adaptive Traffic Signal Digital Twin - AI Adaptive Signal Controller
 * Dynamic decision-making engine using multi-factor priority scoring, queue discharge estimation,
 * starvation prevention, and early green truncation (gap-out).
 */

import { SIM_CONFIG } from '../config.js';

export class AdaptiveAIController {
  constructor(customConfig = {}) {
    this.name = 'AI Adaptive Controller';
    this.type = 'ADAPTIVE';

    // Core Parameters
    this.minGreen = customConfig.minGreen || SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.minGreen;       // 7s
    this.maxGreen = customConfig.maxGreen || SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.maxGreen;       // 45s
    this.yellowDuration = customConfig.yellow || SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.yellowDuration; // 3.5s
    this.allRedDuration = customConfig.allRed || SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.allRedDuration; // 1.5s
    this.saturationHeadway = customConfig.saturationHeadway || SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.saturationHeadway; // 1.8s/veh
    this.startupLostTime = customConfig.startupLostTime || SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.startupLostTime;       // 2.5s
    this.gapOutThreshold = customConfig.gapOutThreshold || SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.gapOutThreshold;       // 2.2s

    // Multi-factor Weights
    this.weights = {
      queueLength: SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.weights.queueLength,
      maxWaitTime: SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.weights.maxWaitTime,
      totalWaitTime: SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.weights.totalWaitTime,
      arrivalRate: SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.weights.arrivalRate,
      starvationMultiplier: SIM_CONFIG.ADAPTIVE_AI_DEFAULTS.weights.starvationMultiplier
    };

    // State machine
    this.activeRoadId = 'A';
    this.nextRoadId = null;
    this.phase = 'GREEN'; // 'GREEN', 'YELLOW', 'ALL_RED'
    this.phaseTimeElapsed = 0;
    this.phaseTimeTotal = 15; // Dynamically computed

    // Consecutive cycle tracking to enforce fairness
    this.consecutiveGreenCount = { A: 0, B: 0, C: 0, D: 0 };
    this.timeSinceLastGreen = { A: 0, B: 0, C: 0, D: 0 };
    this.cycleCount = 0;
    this.totalActiveTime = 0;

    // AI Explainability & Telemetry
    this.decisionHistory = [];
    this.latestDecision = {
      roadSelected: 'A',
      allocatedGreen: 15,
      reason: 'Initial phase start',
      scores: { A: 0, B: 0, C: 0, D: 0 },
      details: {}
    };
  }

  /**
   * Resets controller
   */
  reset() {
    this.activeRoadId = 'A';
    this.nextRoadId = null;
    this.phase = 'GREEN';
    this.phaseTimeElapsed = 0;
    this.phaseTimeTotal = 15;
    this.consecutiveGreenCount = { A: 0, B: 0, C: 0, D: 0 };
    this.timeSinceLastGreen = { A: 0, B: 0, C: 0, D: 0 };
    this.cycleCount = 0;
    this.totalActiveTime = 0;
    this.decisionHistory = [];
  }

  /**
   * Main controller tick
   * @param {number} dt Delta time in seconds
   * @param {Object} roads Map of roads { A: Road, B: Road, C: Road, D: Road }
   * @param {Object} arrivalRates Current arrival rates per road (veh/min)
   */
  update(dt, roads, arrivalRates = {}) {
    this.phaseTimeElapsed += dt;
    this.totalActiveTime += dt;

    // Update starvation timers for roads not currently green
    for (const rId of ['A', 'B', 'C', 'D']) {
      if (rId !== this.activeRoadId || this.phase === 'ALL_RED') {
        this.timeSinceLastGreen[rId] += dt;
      } else {
        this.timeSinceLastGreen[rId] = 0;
      }
    }

    // State machine evaluation
    if (this.phase === 'GREEN') {
      const activeRoad = roads[this.activeRoadId];
      let shouldTerminateEarly = false;

      // Check Intelligent Gap-Out / Early Clearance:
      // If min green has elapsed and active road queue is empty, and sensor is inactive
      if (this.phaseTimeElapsed >= this.minGreen) {
        if (activeRoad && activeRoad.waitingVehiclesCount === 0 && !activeRoad.sensorActive) {
          // Check if any other road has waiting vehicles
          const otherWaiting = Object.values(roads).some(r => r.id !== this.activeRoadId && r.waitingVehiclesCount > 0);
          if (otherWaiting) {
            shouldTerminateEarly = true;
          }
        }
      }

      // Check Emergency Vehicle Preemption:
      // If another road has an emergency vehicle and current green > minGreen, trigger early transition
      let emergencyRoad = null;
      for (const rId of ['A', 'B', 'C', 'D']) {
        if (rId !== this.activeRoadId && this.hasEmergencyVehicle(roads[rId])) {
          emergencyRoad = rId;
          break;
        }
      }

      if (emergencyRoad && this.phaseTimeElapsed >= 4.0) {
        shouldTerminateEarly = true;
      }

      if (this.phaseTimeElapsed >= this.phaseTimeTotal || shouldTerminateEarly) {
        // Transition to Yellow
        this.phase = 'YELLOW';
        this.phaseTimeElapsed = 0;
        this.phaseTimeTotal = this.yellowDuration;

        // Run AI decision engine to select next road and calculate its dynamic green time!
        const decision = this.calculateNextPhase(roads, arrivalRates, emergencyRoad);
        this.nextRoadId = decision.nextRoadId;
        this.allocatedNextGreen = decision.allocatedGreen;
        this.latestDecision = decision;
        this.decisionHistory.unshift({
          timestamp: Math.round(this.totalActiveTime),
          ...decision
        });
        if (this.decisionHistory.length > 25) this.decisionHistory.pop();
      }
    } else if (this.phase === 'YELLOW') {
      if (this.phaseTimeElapsed >= this.phaseTimeTotal) {
        // Transition to All-Red clearance
        this.phase = 'ALL_RED';
        this.phaseTimeElapsed = 0;
        this.phaseTimeTotal = this.allRedDuration;
      }
    } else if (this.phase === 'ALL_RED') {
      if (this.phaseTimeElapsed >= this.phaseTimeTotal) {
        // Transition to Green on the AI-selected road!
        this.activeRoadId = this.nextRoadId || 'A';
        this.nextRoadId = null;
        this.phase = 'GREEN';
        this.phaseTimeElapsed = 0;
        this.phaseTimeTotal = this.allocatedNextGreen || this.minGreen;

        this.consecutiveGreenCount[this.activeRoadId]++;
        for (const rId of ['A', 'B', 'C', 'D']) {
          if (rId !== this.activeRoadId) {
            this.consecutiveGreenCount[rId] = 0;
          }
        }
        this.cycleCount++;
      }
    }

    // Apply signal states to roads
    for (const rId of ['A', 'B', 'C', 'D']) {
      const road = roads[rId];
      if (!road) continue;

      if (this.phase === 'ALL_RED') {
        road.signalState = SIM_CONFIG.SIGNAL_STATES.ALL_RED;
        road.allocatedDuration = this.phaseTimeTotal;
        road.elapsedInPhase = this.phaseTimeElapsed;
        road.remainingInPhase = Math.max(0, this.phaseTimeTotal - this.phaseTimeElapsed);
      } else if (rId === this.activeRoadId) {
        road.signalState = (this.phase === 'YELLOW') ? SIM_CONFIG.SIGNAL_STATES.YELLOW : SIM_CONFIG.SIGNAL_STATES.GREEN;
        road.allocatedDuration = this.phaseTimeTotal;
        road.elapsedInPhase = this.phaseTimeElapsed;
        road.remainingInPhase = Math.max(0, this.phaseTimeTotal - this.phaseTimeElapsed);
      } else {
        road.signalState = SIM_CONFIG.SIGNAL_STATES.RED;
        road.allocatedDuration = 0;
        road.elapsedInPhase = 0;
        // Remaining red time is dynamically estimated
        road.remainingInPhase = (this.nextRoadId === rId) 
          ? Math.max(0, (this.phase === 'YELLOW' ? this.yellowDuration - this.phaseTimeElapsed : 0) + this.allRedDuration)
          : Math.max(5, Math.round(this.phaseTimeTotal - this.phaseTimeElapsed + 10));
      }
    }
  }

  /**
   * Checks if a road has an active emergency vehicle approaching or waiting
   */
  hasEmergencyVehicle(road) {
    if (!road) return false;
    for (const lane of road.lanes) {
      for (const v of lane) {
        if (v.isEmergency && !v.hasCrossedStopLine) return true;
      }
    }
    return false;
  }

  /**
   * AI Decision Engine: Evaluates multi-factor priority for all roads, enforces fairness,
   * prevents starvation, and calculates optimal green duration.
   */
  calculateNextPhase(roads, arrivalRates, emergencyRoadOverride = null) {
    const roadIds = ['A', 'B', 'C', 'D'];
    const scores = {};
    const details = {};

    // If an emergency vehicle has arrived, instant preemption override
    if (emergencyRoadOverride) {
      for (const rId of roadIds) {
        scores[rId] = (rId === emergencyRoadOverride) ? 9999 : 0;
      }
      const green = this.calculateGreenDuration(roads[emergencyRoadOverride].waitingVehiclesCount);
      return {
        nextRoadId: emergencyRoadOverride,
        allocatedGreen: green,
        reason: `EMERGENCY PREEMPTION: Priority vehicle detected on Road ${emergencyRoadOverride}`,
        scores,
        details: { emergency: true }
      };
    }

    // Compute multi-factor scores for each candidate road
    for (const rId of roadIds) {
      const road = roads[rId];
      const q = road ? road.waitingVehiclesCount : 0;
      const maxW = road ? road.maxWaitTimeSec : 0;
      const totalW = road ? road.totalWaitTimeSec : 0;
      const rate = arrivalRates[rId] || 15;
      const unservedTime = this.timeSinceLastGreen[rId] || 0;
      const consecutive = this.consecutiveGreenCount[rId] || 0;

      // 1. Queue Component (Weight 1.2)
      const qScore = q * this.weights.queueLength * 2.5;

      // 2. Maximum Wait Time Component (Weight 1.5)
      const maxWaitScore = maxW * this.weights.maxWaitTime;

      // 3. Total Accumulated Wait Time (Weight 0.6)
      const totalWaitScore = (totalW / 8) * this.weights.totalWaitTime;

      // 4. Inbound Flow / Arrival Rate (Weight 0.4)
      const arrivalScore = (rate / 10) * this.weights.arrivalRate;

      // 5. Starvation Prevention & Fairness Factor:
      // Exponential penalty if road has been neglected for too long
      let starvationBonus = 0;
      if (unservedTime > 30.0 && q > 0) {
        starvationBonus = Math.pow(unservedTime / 25.0, 2.2) * 15.0 * this.weights.starvationMultiplier;
      }

      // 6. Anti-Monopoly Penalty:
      // Prevent the currently active road from staying green perpetually if other roads have waiting vehicles
      let monopolyPenalty = 0;
      if (rId === this.activeRoadId && consecutive >= 1) {
        const othersWaiting = roadIds.some(other => other !== rId && roads[other] && roads[other].waitingVehiclesCount > 0);
        if (othersWaiting) {
          monopolyPenalty = 40.0 * consecutive;
        }
      }

      // Bonus if queue is zero but there is impending arrival on loop sensor
      let sensorBonus = (road && road.sensorActive && q === 0) ? 8 : 0;

      const totalScore = Math.max(0, qScore + maxWaitScore + totalWaitScore + arrivalScore + starvationBonus + sensorBonus - monopolyPenalty);
      
      scores[rId] = Math.round(totalScore * 10) / 10;
      if (road) road.priorityScore = scores[rId];

      details[rId] = {
        queue: q,
        maxWait: Math.round(maxW),
        unservedTime: Math.round(unservedTime),
        qScore: Math.round(qScore),
        starvationBonus: Math.round(starvationBonus),
        totalScore: scores[rId]
      };
    }

    // Select road with highest priority score
    let selectedRoad = roadIds[0];
    let highestScore = -1;

    // Sort candidates
    const sortedCandidates = [...roadIds].sort((a, b) => scores[b] - scores[a]);
    selectedRoad = sortedCandidates[0];
    highestScore = scores[selectedRoad];

    // If all scores are 0 (quiet intersection), cycle to next in round-robin
    if (highestScore <= 0.5) {
      const curIdx = roadIds.indexOf(this.activeRoadId);
      selectedRoad = roadIds[(curIdx + 1) % roadIds.length];
    }

    // Calculate dynamically tailored green duration for the selected road
    const targetRoad = roads[selectedRoad];
    const queueToClear = targetRoad ? targetRoad.waitingVehiclesCount : 0;
    const allocatedGreen = this.calculateGreenDuration(queueToClear);

    // Formulate human-readable reasoning
    let reason = '';
    const selDetail = details[selectedRoad];
    if (selDetail && selDetail.starvationBonus > 25) {
      reason = `Fairness Trigger: Road ${selectedRoad} waiting ${selDetail.unservedTime}s (+${selDetail.starvationBonus} starvation bonus)`;
    } else if (queueToClear > 0) {
      reason = `Congestion Priority: Road ${selectedRoad} has highest queue (${queueToClear} vehicles, score: ${highestScore})`;
    } else {
      reason = `Standard Cycle: Road ${selectedRoad} scheduled (low demand)`;
    }

    return {
      nextRoadId: selectedRoad,
      allocatedGreen,
      reason,
      scores,
      details
    };
  }

  /**
   * Dynamically calculates green duration to discharge queue based on saturation flow rate.
   * Clamped between minGreen and maxGreen.
   */
  calculateGreenDuration(queueCount) {
    if (queueCount <= 1) {
      return this.minGreen; // 7 sec minimum
    }

    // Two lanes discharge simultaneously: effective discharge is queueCount / 2
    const vehiclesPerLane = Math.ceil(queueCount / 2);
    // Green duration = Startup lost time + (Vehicles per lane * saturation headway)
    const neededTime = this.startupLostTime + (vehiclesPerLane * this.saturationHeadway);

    // Clamp within safety envelopes [minGreen, maxGreen]
    return Math.round(Math.min(this.maxGreen, Math.max(this.minGreen, neededTime)));
  }

  /**
   * Returns metadata for UI inspector
   */
  getInfo() {
    return {
      name: this.name,
      type: this.type,
      activeRoad: this.activeRoadId,
      nextRoad: this.nextRoadId,
      phase: this.phase,
      timeElapsed: Math.round(this.phaseTimeElapsed * 10) / 10,
      timeTotal: Math.round(this.phaseTimeTotal * 10) / 10,
      cycleCount: this.cycleCount,
      minGreen: this.minGreen,
      maxGreen: this.maxGreen,
      latestDecision: this.latestDecision,
      decisionHistory: this.decisionHistory
    };
  }
}
