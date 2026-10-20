/**
 * AI Adaptive Traffic Signal Digital Twin - Road & Approach Model
 */

import { SIM_CONFIG } from '../config.js';

export class Road {
  constructor(id, name, direction, approachFrom) {
    this.id = id;                     // 'A', 'B', 'C', 'D'
    this.name = name;                 // e.g. "Road A (North)"
    this.direction = direction;       // 'N', 'E', 'S', 'W'
    this.approachFrom = approachFrom; // Compass origin
    
    // Signal state & timing
    this.signalState = SIM_CONFIG.SIGNAL_STATES.RED;
    this.allocatedDuration = 0;       // Duration of current phase in seconds
    this.elapsedInPhase = 0;          // Seconds elapsed in current phase
    this.remainingInPhase = 0;        // Seconds remaining in current phase

    // Lanes storage: 2 inbound lanes
    // Lane 0: Outer lane (Straight or Right)
    // Lane 1: Inner lane (Straight or Left)
    this.lanes = [[], []];

    // Real-time telemetry metrics
    this.waitingVehiclesCount = 0;    // Number of stationary vehicles in queue
    this.queueLengthMeters = 0;       // Queue length in meters (~0.2m per px)
    this.maxWaitTimeSec = 0;          // Longest wait time of any vehicle currently queued
    this.totalWaitTimeSec = 0;        // Sum of wait time of currently queued vehicles
    this.totalVehiclesPassed = 0;     // Total vehicles that crossed stop line
    this.cumulativeWaitTime = 0;      // Sum of wait times for all vehicles that passed
    this.avgWaitTimeSec = 0;          // Average wait time of cleared vehicles
    this.sensorActive = false;        // Inductive loop detection trigger
    this.priorityScore = 0;           // AI calculated priority score
    this.timeSinceLastGreen = 0;      // Seconds since this road last had green (starvation tracker)
  }

  /**
   * Resets road metrics and clears all vehicles
   */
  reset() {
    this.signalState = SIM_CONFIG.SIGNAL_STATES.RED;
    this.allocatedDuration = 0;
    this.elapsedInPhase = 0;
    this.remainingInPhase = 0;
    this.lanes = [[], []];
    this.waitingVehiclesCount = 0;
    this.queueLengthMeters = 0;
    this.maxWaitTimeSec = 0;
    this.totalWaitTimeSec = 0;
    this.totalVehiclesPassed = 0;
    this.cumulativeWaitTime = 0;
    this.avgWaitTimeSec = 0;
    this.sensorActive = false;
    this.priorityScore = 0;
    this.timeSinceLastGreen = 0;
  }

  /**
   * Updates road telemetry metrics based on currently present vehicles
   */
  updateTelemetry(dt) {
    if (this.signalState !== SIM_CONFIG.SIGNAL_STATES.GREEN) {
      this.timeSinceLastGreen += dt;
    } else {
      this.timeSinceLastGreen = 0;
    }

    let waitingCount = 0;
    let maxWait = 0;
    let sumWait = 0;
    let loopDetected = false;

    const stopS = SIM_CONFIG.SPAWN_OFFSET - SIM_CONFIG.STOP_LINE_OFFSET;
    const sensorStart = SIM_CONFIG.SPAWN_OFFSET - SIM_CONFIG.SENSOR_LOOP_OFFSET;
    const sensorEnd = sensorStart + SIM_CONFIG.SENSOR_LOOP_LENGTH;

    for (let l = 0; l < this.lanes.length; l++) {
      const lane = this.lanes[l];
      for (let i = 0; i < lane.length; i++) {
        const v = lane[i];
        
        // Sensor loop occupancy check
        if (v.s >= sensorStart - v.length && v.s <= sensorEnd) {
          loopDetected = true;
        }

        // Waiting queue check: vehicle is before stop line and is stopped or moving very slowly (< 4 px/s)
        if (!v.hasCrossedStopLine && v.s <= stopS + 5 && v.speed < 5.0) {
          waitingCount++;
          sumWait += v.waitTime;
          if (v.waitTime > maxWait) {
            maxWait = v.waitTime;
          }
        }
      }
    }

    this.waitingVehiclesCount = waitingCount;
    // Approximating queue length: average car length + gap is ~40px (~8 meters in scale)
    this.queueLengthMeters = Math.round(waitingCount * 7.5);
    this.maxWaitTimeSec = Math.round(maxWait * 10) / 10;
    this.totalWaitTimeSec = Math.round(sumWait * 10) / 10;
    this.sensorActive = loopDetected;

    if (this.totalVehiclesPassed > 0) {
      this.avgWaitTimeSec = Math.round((this.cumulativeWaitTime / this.totalVehiclesPassed) * 10) / 10;
    }
  }

  /**
   * Registers a vehicle passing the stop line
   */
  onVehiclePassed(vehicle) {
    this.totalVehiclesPassed++;
    this.cumulativeWaitTime += vehicle.waitTime;
  }
}
