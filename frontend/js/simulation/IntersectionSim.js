/**
 * AI Adaptive Traffic Signal Digital Twin - Single Intersection Simulation Instance
 */

import { SIM_CONFIG } from '../config.js';
import { Road } from '../models/Road.js';
import { Vehicle } from '../models/Vehicle.js';

export class IntersectionSim {
  constructor(id, name, controller) {
    this.id = id;
    this.name = name;
    this.controller = controller;

    // Roads initialization
    this.roads = {
      A: new Road('A', SIM_CONFIG.ROADS.NORTH.name, 'N', 'N'),
      B: new Road('B', SIM_CONFIG.ROADS.EAST.name,  'E', 'E'),
      C: new Road('C', SIM_CONFIG.ROADS.SOUTH.name, 'S', 'S'),
      D: new Road('D', SIM_CONFIG.ROADS.WEST.name,  'W', 'W')
    };

    // Active vehicles collection
    this.vehicles = [];

    // Simulation metrics & statistics
    this.simTime = 0;
    this.totalSpawned = 0;
    this.totalPassed = 0;
    this.totalExited = 0;
    
    this.totalWaitTime = 0;     // Sum of wait time of all passed vehicles
    this.avgWaitTime = 0;       // Average wait time of cleared vehicles
    this.maxWaitTimeObserved = 0;
    this.currentTotalQueue = 0;
    this.peakQueueObserved = 0;
    this.totalQueueMeters = 0;
    
    this.throughputPerMin = 0;
    this.fuelWastedLiters = 0;  // Idle fuel burned
    this.co2EmissionsKg = 0;    // CO2 emitted from idling

    // Telemetry time-series history (for charts)
    this.history = {
      time: [],
      avgWaitTime: [],
      queueLength: [],
      throughput: [],
      cumulativeCleared: []
    };
    this.historySampleTimer = 0;
    this.historySampleInterval = 1.0; // Sample every 1 sim-second
  }

  /**
   * Resets simulation instance to blank state
   */
  reset() {
    this.simTime = 0;
    this.totalSpawned = 0;
    this.totalPassed = 0;
    this.totalExited = 0;
    this.totalWaitTime = 0;
    this.avgWaitTime = 0;
    this.maxWaitTimeObserved = 0;
    this.currentTotalQueue = 0;
    this.peakQueueObserved = 0;
    this.totalQueueMeters = 0;
    this.throughputPerMin = 0;
    this.fuelWastedLiters = 0;
    this.co2EmissionsKg = 0;

    for (const rId of ['A', 'B', 'C', 'D']) {
      this.roads[rId].reset();
    }
    this.vehicles = [];
    this.controller.reset();

    this.history = {
      time: [],
      avgWaitTime: [],
      queueLength: [],
      throughput: [],
      cumulativeCleared: []
    };
    this.historySampleTimer = 0;
  }

  /**
   * Spawns a vehicle if spawn area in target lane is clear
   */
  spawnVehicle(spec) {
    const road = this.roads[spec.roadId];
    if (!road) return null;

    const lane = road.lanes[spec.laneIndex];
    // Check if space at spawn point (s = 0) is blocked by a recent car
    for (let i = 0; i < lane.length; i++) {
      if (lane[i].s < 45) {
        // Space occupied, defer or cancel spawn
        return null;
      }
    }

    const vehicle = new Vehicle({
      ...spec,
      spawnTime: this.simTime
    });

    lane.push(vehicle);
    this.vehicles.push(vehicle);
    this.totalSpawned++;
    return vehicle;
  }

  /**
   * Advances simulation by dt seconds
   * @param {number} dt Delta time in seconds
   * @param {Object} arrivalRates Arrival rates per road (veh/min) for AI controller
   */
  update(dt, arrivalRates = {}) {
    this.simTime += dt;

    // 1. Update Traffic Signal Controller
    this.controller.update(dt, this.roads, arrivalRates);

    // 2. Update vehicles in each lane
    for (const rId of ['A', 'B', 'C', 'D']) {
      const road = this.roads[rId];
      const signalState = road.signalState;

      for (let l = 0; l < road.lanes.length; l++) {
        const lane = road.lanes[l];

        // Sort lane vehicles from furthest forward (highest s) to newest (lowest s)
        lane.sort((a, b) => b.s - a.s);

        for (let i = 0; i < lane.length; i++) {
          const v = lane[i];
          const leadVehicle = (i > 0) ? lane[i - 1] : null;

          const previouslyCrossed = v.hasCrossedStopLine;
          v.update(dt, leadVehicle, signalState, this.simTime);
          v.computeWorldTransform();

          // Check if vehicle just crossed stop line
          if (!previouslyCrossed && v.hasCrossedStopLine) {
            this.totalPassed++;
            this.totalWaitTime += v.waitTime;
            road.onVehiclePassed(v);

            if (v.waitTime > this.maxWaitTimeObserved) {
              this.maxWaitTimeObserved = v.waitTime;
            }
          }
        }
      }

      // Update road statistics
      road.updateTelemetry(dt);
    }

    // 3. Remove vehicles that have finished traversing intersection
    this.vehicles = this.vehicles.filter(v => {
      if (v.hasExited) {
        this.totalExited++;
        // Remove from road lane array
        const road = this.roads[v.roadId];
        if (road) {
          const lane = road.lanes[v.laneIndex];
          const idx = lane.indexOf(v);
          if (idx !== -1) lane.splice(idx, 1);
        }
        return false;
      }
      return true;
    });

    // 4. Aggregate global metrics
    let currentQueue = 0;
    let queueMeters = 0;
    for (const rId of ['A', 'B', 'C', 'D']) {
      currentQueue += this.roads[rId].waitingVehiclesCount;
      queueMeters += this.roads[rId].queueLengthMeters;
    }

    this.currentTotalQueue = currentQueue;
    this.totalQueueMeters = queueMeters;
    if (currentQueue > this.peakQueueObserved) {
      this.peakQueueObserved = currentQueue;
    }

    if (this.totalPassed > 0) {
      this.avgWaitTime = Math.round((this.totalWaitTime / this.totalPassed) * 10) / 10;
    }

    // Live throughput (vehicles / min)
    if (this.simTime > 5) {
      this.throughputPerMin = Math.round((this.totalPassed / (this.simTime / 60)) * 10) / 10;
    }

    // Environmental metrics based on accumulated waiting hours
    // (sum of wait times of currently waiting and cleared vehicles)
    let totalIdleHours = (this.totalWaitTime + (currentQueue * dt)) / 3600.0;
    this.fuelWastedLiters = Math.round(totalIdleHours * SIM_CONFIG.ENVIRONMENTAL.IDLE_FUEL_LITER_PER_HOUR * 100) / 100;
    this.co2EmissionsKg = Math.round(this.fuelWastedLiters * SIM_CONFIG.ENVIRONMENTAL.IDLE_CO2_KG_PER_LITER * 100) / 100;

    // 5. Sample time-series history
    this.historySampleTimer += dt;
    if (this.historySampleTimer >= this.historySampleInterval) {
      this.historySampleTimer = 0;
      this.sampleTelemetry();
    }
  }

  /**
   * Samples current statistics for graph rendering
   */
  sampleTelemetry() {
    this.history.time.push(Math.round(this.simTime));
    this.history.avgWaitTime.push(this.avgWaitTime);
    this.history.queueLength.push(this.currentTotalQueue);
    this.history.throughput.push(this.throughputPerMin);
    this.history.cumulativeCleared.push(this.totalPassed);

    // Keep up to 120 history samples (last 2 minutes of real-time)
    if (this.history.time.length > 120) {
      this.history.time.shift();
      this.history.avgWaitTime.shift();
      this.history.queueLength.shift();
      this.history.throughput.shift();
      this.history.cumulativeCleared.shift();
    }
  }

  /**
   * Finds a vehicle near given world coordinates (for mouse inspection)
   */
  findVehicleAt(wx, wy, radius = 25) {
    for (const v of this.vehicles) {
      let dx = v.x - wx;
      let dy = v.y - wy;
      if (Math.sqrt(dx * dx + dy * dy) <= radius) {
        return v;
      }
    }
    return null;
  }
}
