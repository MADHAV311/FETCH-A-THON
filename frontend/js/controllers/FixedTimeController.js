/**
 * AI Adaptive Traffic Signal Digital Twin - Fixed-Time Traffic Controller
 * Strict cyclic time-based signal controller without dynamic traffic feedback.
 */

import { SIM_CONFIG } from '../config.js';

export class FixedTimeController {
  constructor(customConfig = {}) {
    this.name = 'Fixed-Time Controller';
    this.type = 'FIXED';
    
    // Timings
    this.greenDurations = {
      A: customConfig.greenA || SIM_CONFIG.FIXED_TIME_DEFAULTS.greenDuration.A,
      B: customConfig.greenB || SIM_CONFIG.FIXED_TIME_DEFAULTS.greenDuration.B,
      C: customConfig.greenC || SIM_CONFIG.FIXED_TIME_DEFAULTS.greenDuration.C,
      D: customConfig.greenD || SIM_CONFIG.FIXED_TIME_DEFAULTS.greenDuration.D
    };
    this.yellowDuration = customConfig.yellow || SIM_CONFIG.FIXED_TIME_DEFAULTS.yellowDuration;
    this.allRedDuration = customConfig.allRed || SIM_CONFIG.FIXED_TIME_DEFAULTS.allRedDuration;

    // Cycle order: A -> B -> C -> D
    this.cycle = ['A', 'B', 'C', 'D'];
    this.currentCycleIndex = 0; // Starts with Road A
    
    // Internal state: 'GREEN', 'YELLOW', 'ALL_RED'
    this.phase = 'GREEN';
    this.phaseTimeElapsed = 0;
    this.phaseTimeTotal = this.greenDurations[this.cycle[0]];
    
    this.cycleCount = 0;
    this.totalActiveTime = 0;
  }

  /**
   * Resets controller to initial state
   */
  reset() {
    this.currentCycleIndex = 0;
    this.phase = 'GREEN';
    this.phaseTimeElapsed = 0;
    this.phaseTimeTotal = this.greenDurations[this.cycle[0]];
    this.cycleCount = 0;
    this.totalActiveTime = 0;
  }

  /**
   * Sets green duration for a specific road
   */
  setRoadGreenDuration(roadId, seconds) {
    if (this.greenDurations[roadId] !== undefined) {
      this.greenDurations[roadId] = Math.max(5, Math.min(120, seconds));
    }
  }

  /**
   * Ticks the controller and updates roads' signal states
   * @param {number} dt Delta time in seconds
   * @param {Object} roads Map of roads { A: Road, B: Road, C: Road, D: Road }
   */
  update(dt, roads) {
    this.phaseTimeElapsed += dt;
    this.totalActiveTime += dt;

    const currentRoadId = this.cycle[this.currentCycleIndex];

    // State machine transitions
    if (this.phase === 'GREEN') {
      if (this.phaseTimeElapsed >= this.phaseTimeTotal) {
        // Transition to Yellow
        this.phase = 'YELLOW';
        this.phaseTimeElapsed = 0;
        this.phaseTimeTotal = this.yellowDuration;
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
        // Transition to next road in cycle
        this.currentCycleIndex = (this.currentCycleIndex + 1) % this.cycle.length;
        if (this.currentCycleIndex === 0) {
          this.cycleCount++;
        }
        
        const nextRoadId = this.cycle[this.currentCycleIndex];
        this.phase = 'GREEN';
        this.phaseTimeElapsed = 0;
        this.phaseTimeTotal = this.greenDurations[nextRoadId];
      }
    }

    // Apply computed signal states to all roads
    const activeRoad = this.cycle[this.currentCycleIndex];
    for (const rId of this.cycle) {
      const road = roads[rId];
      if (!road) continue;

      if (this.phase === 'ALL_RED') {
        road.signalState = SIM_CONFIG.SIGNAL_STATES.ALL_RED;
        road.allocatedDuration = this.phaseTimeTotal;
        road.elapsedInPhase = this.phaseTimeElapsed;
        road.remainingInPhase = Math.max(0, this.phaseTimeTotal - this.phaseTimeElapsed);
      } else if (rId === activeRoad) {
        road.signalState = (this.phase === 'YELLOW') ? SIM_CONFIG.SIGNAL_STATES.YELLOW : SIM_CONFIG.SIGNAL_STATES.GREEN;
        road.allocatedDuration = this.phaseTimeTotal;
        road.elapsedInPhase = this.phaseTimeElapsed;
        road.remainingInPhase = Math.max(0, this.phaseTimeTotal - this.phaseTimeElapsed);
      } else {
        road.signalState = SIM_CONFIG.SIGNAL_STATES.RED;
        // Estimate time until green for waiting countdown
        road.allocatedDuration = 0;
        road.elapsedInPhase = 0;
        road.remainingInPhase = this.calculateRemainingRedTime(rId);
      }
    }
  }

  /**
   * Computes remaining red duration for a given road
   */
  calculateRemainingRedTime(roadId) {
    let activeRoadId = this.cycle[this.currentCycleIndex];
    if (roadId === activeRoadId && this.phase !== 'ALL_RED') {
      return 0;
    }

    let remaining = Math.max(0, this.phaseTimeTotal - this.phaseTimeElapsed);
    let idx = (this.currentCycleIndex + (this.phase === 'ALL_RED' ? 1 : 0)) % this.cycle.length;

    // Sum intermediate green + yellow + red intervals until roadId
    while (this.cycle[idx] !== roadId) {
      let r = this.cycle[idx];
      remaining += this.greenDurations[r] + this.yellowDuration + this.allRedDuration;
      idx = (idx + 1) % this.cycle.length;
    }

    return Math.round(remaining);
  }

  /**
   * Returns metadata for UI inspection
   */
  getInfo() {
    return {
      name: this.name,
      type: this.type,
      activeRoad: this.cycle[this.currentCycleIndex],
      phase: this.phase,
      timeElapsed: Math.round(this.phaseTimeElapsed * 10) / 10,
      timeTotal: Math.round(this.phaseTimeTotal * 10) / 10,
      cycleCount: this.cycleCount,
      fixedTimings: { ...this.greenDurations }
    };
  }
}
