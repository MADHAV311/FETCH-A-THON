/**
 * AI Adaptive Traffic Signal Digital Twin - Vehicle Entity Model
 */

import { SIM_CONFIG } from '../config.js';

let globalVehicleCounter = 1;

export class Vehicle {
  constructor(spec) {
    this.id = spec.id || `V-${globalVehicleCounter++}`;
    this.typeSpec = spec.typeSpec;
    this.roadId = spec.roadId;     // 'A', 'B', 'C', or 'D'
    this.laneIndex = spec.laneIndex !== undefined ? spec.laneIndex : 0; // 0: outer (right/straight), 1: inner (left/straight)
    this.intendedManeuver = spec.intendedManeuver || 'STRAIGHT'; // 'STRAIGHT', 'RIGHT', 'LEFT'
    
    // Physical dimensions & limits
    this.length = this.typeSpec.length;
    this.width = this.typeSpec.width;
    this.color = spec.color || this.typeSpec.colors[Math.floor(Math.random() * this.typeSpec.colors.length)];
    this.isEmergency = !!this.typeSpec.isEmergency;
    
    // Dynamic physics
    this.maxSpeed = this.typeSpec.maxSpeed;
    this.accel = this.typeSpec.accel;
    this.decel = this.typeSpec.decel;
    this.speed = spec.initialSpeed || this.maxSpeed * 0.75;
    
    // Longitudinal coordinate s: distance traveled along the inbound approach from spawn
    // s = 0: spawn point (~480px from center)
    // s = stopLineS: stop bar
    // s > stopLineS: intersection traversal & exit
    this.s = spec.s || 0;
    this.totalApproachDistance = SIM_CONFIG.SPAWN_OFFSET;
    this.stopLineS = this.totalApproachDistance - SIM_CONFIG.STOP_LINE_OFFSET;
    
    // Traversal state
    this.hasCrossedStopLine = false;
    this.isInsideIntersection = false;
    this.hasExited = false;
    
    // Telemetry & metrics
    this.spawnTime = spec.spawnTime || 0;
    this.waitTime = 0;             // Accumulated time stopped (speed < 3 px/s)
    this.isStopped = false;
    this.totalDistanceTraveled = 0;
    this.clearanceTime = null;

    // Visual indicators
    this.brakeLightsOn = false;
    this.turnSignalTimer = 0;
    this.turnSignalOn = false;
    this.sirenPhase = 0;
    
    // Current world coordinates & orientation
    this.x = 0;
    this.y = 0;
    this.angle = 0; // In radians
  }

  /**
   * Updates vehicle motion using Intelligent Driver Model (IDM) & intersection rules.
   * @param {number} dt Delta time in seconds
   * @param {Vehicle|null} leadVehicle Vehicle directly ahead in the same lane
   * @param {string} signalState 'RED', 'YELLOW', 'GREEN', or 'ALL_RED'
   * @param {number} currentTime Total simulation time in seconds
   */
  update(dt, leadVehicle, signalState, currentTime) {
    if (this.hasExited) return;

    // Track waiting time when practically stationary
    if (this.speed < 4.0) {
      this.waitTime += dt;
      this.isStopped = true;
    } else {
      this.isStopped = false;
    }

    // Determine target acceleration based on IDM (Intelligent Driver Model)
    let desiredAccel = this.calculateIDMAcceleration(dt, leadVehicle, signalState);

    // Update speed and apply physical limits
    this.speed = Math.max(0, this.speed + desiredAccel * dt);
    
    // Visual brake light trigger
    this.brakeLightsOn = desiredAccel < -15 || this.isStopped;

    // Advance longitudinal distance s
    let ds = this.speed * dt;
    this.s += ds;
    this.totalDistanceTraveled += ds;

    // Check intersection milestone crossings
    if (!this.hasCrossedStopLine && this.s >= this.stopLineS) {
      this.hasCrossedStopLine = true;
      this.isInsideIntersection = true;
    }

    // Check exit point
    let exitThreshold = this.totalApproachDistance + 350;
    if (this.s >= exitThreshold) {
      this.hasExited = true;
      this.isInsideIntersection = false;
      if (!this.clearanceTime) {
        this.clearanceTime = currentTime;
      }
    }

    // Turn indicator blinker
    if (this.intendedManeuver !== 'STRAIGHT') {
      this.turnSignalTimer += dt;
      if (this.turnSignalTimer > 0.35) {
        this.turnSignalTimer = 0;
        this.turnSignalOn = !this.turnSignalOn;
      }
    }

    // Emergency siren strobe
    if (this.isEmergency) {
      this.sirenPhase = (this.sirenPhase + dt * 10) % (Math.PI * 2);
    }
  }

  /**
   * Calculates longitudinal acceleration based on the Intelligent Driver Model (IDM)
   */
  calculateIDMAcceleration(dt, leadVehicle, signalState) {
    const v = this.speed;
    const v0 = this.maxSpeed;
    const a = this.accel;
    const b = this.decel;
    const s0 = SIM_CONFIG.STANDSTILL_GAP;
    const T = SIM_CONFIG.TIME_HEADWAY;

    // Free-road acceleration component
    let freeRoadTerm = a * (1 - Math.pow(v / v0, 4));

    // Interaction with lead vehicle
    let interactionTerm = 0;
    if (leadVehicle && leadVehicle.s > this.s) {
      let gap = (leadVehicle.s - leadVehicle.length) - this.s;
      let deltaV = v - leadVehicle.speed;
      
      // Desired dynamic minimum gap s*(v, deltaV)
      let sStar = s0 + Math.max(0, v * T + (v * deltaV) / (2 * Math.sqrt(a * b)));
      interactionTerm = -a * Math.pow(sStar / Math.max(gap, 0.5), 2);
    }

    // Interaction with Traffic Signal / Stop Line
    let signalTerm = 0;
    if (!this.hasCrossedStopLine) {
      let distToStop = this.stopLineS - this.s;

      if (distToStop > -5) {
        let mustStop = false;

        if (signalState === SIM_CONFIG.SIGNAL_STATES.RED || signalState === SIM_CONFIG.SIGNAL_STATES.ALL_RED) {
          mustStop = true;
        } else if (signalState === SIM_CONFIG.SIGNAL_STATES.YELLOW) {
          // Yellow decision dilemma zone:
          // If car is far away and can stop comfortably, stop. If already too close to safely stop, proceed.
          let stoppingDistance = (v * v) / (2 * b);
          if (distToStop > stoppingDistance * 1.1 && distToStop > 25) {
            mustStop = true;
          }
        }

        // Emergency vehicles override red if intersection is clear, but slow down for safety
        if (this.isEmergency && mustStop) {
          if (distToStop > 40) {
            mustStop = false; // Emergency vehicle pushes through
          }
        }

        if (mustStop) {
          let deltaV = v;
          let sStar = s0 + Math.max(0, v * T + (v * deltaV) / (2 * Math.sqrt(a * b)));
          let stopGap = Math.max(distToStop, 0.5);
          let stopDecel = -a * Math.pow(sStar / stopGap, 2);
          
          if (stopDecel < signalTerm) {
            signalTerm = stopDecel;
          }
        }
      }
    }

    let totalAccel = freeRoadTerm + interactionTerm + signalTerm;
    // Cap deceleration to realistic vehicle physical limits
    return Math.max(-SIM_CONFIG.HARD_BRAKING, Math.min(a, totalAccel));
  }

  /**
   * Computes vehicle's 2D world position (x, y) and heading angle based on road geometry.
   * Coordinate origin (0, 0) is at the center of the intersection.
   */
  computeWorldTransform() {
    // Lane offset from centerline:
    // Lane 0 (outer curb): 52.5px
    // Lane 1 (inner): 17.5px
    const laneOffset = (this.laneIndex === 0 ? 52.5 : 17.5);
    const approachDist = this.totalApproachDistance;
    const stopS = this.stopLineS;

    let wx = 0;
    let wy = 0;
    let wAngle = 0;

    if (this.s <= stopS) {
      const distFromCenter = approachDist - this.s;

      switch (this.roadId) {
        case 'A': // North approaching South
          wx = -laneOffset;
          wy = -distFromCenter;
          wAngle = Math.PI / 2;
          break;
        case 'B': // East approaching West
          wx = distFromCenter;
          wy = -laneOffset;
          wAngle = Math.PI;
          break;
        case 'C': // South approaching North
          wx = laneOffset;
          wy = distFromCenter;
          wAngle = -Math.PI / 2;
          break;
        case 'D': // West approaching East
          wx = -distFromCenter;
          wy = laneOffset;
          wAngle = 0;
          break;
      }
    } else {
      const sPast = this.s - stopS;

      if (this.intendedManeuver === 'STRAIGHT') {
        switch (this.roadId) {
          case 'A': wx = -laneOffset; wy = -75 + sPast; wAngle = Math.PI / 2; break;
          case 'B': wx = 75 - sPast; wy = -laneOffset; wAngle = Math.PI; break;
          case 'C': wx = laneOffset; wy = 75 - sPast; wAngle = -Math.PI / 2; break;
          case 'D': wx = -75 + sPast; wy = laneOffset; wAngle = 0; break;
        }
      } else if (this.intendedManeuver === 'RIGHT') {
        const R = 22.5;
        const arc = (Math.PI / 2) * R;

        if (sPast < arc) {
          const u = sPast / arc;
          const alpha = u * (Math.PI / 2);

          switch (this.roadId) {
            case 'A':
              wx = -75 + R * Math.cos(alpha);
              wy = -75 + R * Math.sin(alpha);
              wAngle = (Math.PI / 2) + alpha;
              break;
            case 'B':
              wx = 75 - R * Math.sin(alpha);
              wy = -75 + R * Math.cos(alpha);
              wAngle = Math.PI + alpha;
              break;
            case 'C':
              wx = 75 - R * Math.cos(alpha);
              wy = 75 - R * Math.sin(alpha);
              wAngle = (-Math.PI / 2) + alpha;
              break;
            case 'D':
              wx = -75 + R * Math.sin(alpha);
              wy = 75 - R * Math.cos(alpha);
              wAngle = alpha;
              break;
          }
        } else {
          const sExit = sPast - arc;
          switch (this.roadId) {
            case 'A': wx = -75 - sExit; wy = -52.5; wAngle = Math.PI; break;
            case 'B': wx = 52.5; wy = -75 - sExit; wAngle = -Math.PI / 2; break;
            case 'C': wx = 75 + sExit; wy = 52.5; wAngle = 0; break;
            case 'D': wx = -52.5; wy = 75 + sExit; wAngle = Math.PI / 2; break;
          }
        }
      } else if (this.intendedManeuver === 'LEFT') {
        const R = 92.5;
        const arc = (Math.PI / 2) * R;

        if (sPast < arc) {
          const u = sPast / arc;
          const alpha = u * (Math.PI / 2);

          switch (this.roadId) {
            case 'A':
              wx = 75 - R * Math.cos(alpha);
              wy = -75 + R * Math.sin(alpha);
              wAngle = (Math.PI / 2) - alpha;
              break;
            case 'B':
              wx = 75 - R * Math.sin(alpha);
              wy = 75 - R * Math.cos(alpha);
              wAngle = Math.PI - alpha;
              break;
            case 'C':
              wx = -75 + R * Math.cos(alpha);
              wy = 75 - R * Math.sin(alpha);
              wAngle = (-Math.PI / 2) - alpha;
              break;
            case 'D':
              wx = -75 + R * Math.sin(alpha);
              wy = -75 + R * Math.cos(alpha);
              wAngle = -alpha;
              break;
          }
        } else {
          const sExit = sPast - arc;
          switch (this.roadId) {
            case 'A': wx = 75 + sExit; wy = 17.5; wAngle = 0; break;
            case 'B': wx = -17.5; wy = 75 + sExit; wAngle = Math.PI / 2; break;
            case 'C': wx = -75 - sExit; wy = -17.5; wAngle = Math.PI; break;
            case 'D': wx = 17.5; wy = -75 - sExit; wAngle = -Math.PI / 2; break;
          }
        }
      } else {
        switch (this.roadId) {
          case 'A': wx = -laneOffset; wy = -75 + sPast; wAngle = Math.PI / 2; break;
          case 'B': wx = 75 - sPast; wy = -laneOffset; wAngle = Math.PI; break;
          case 'C': wx = laneOffset; wy = 75 - sPast; wAngle = -Math.PI / 2; break;
          case 'D': wx = -75 + sPast; wy = laneOffset; wAngle = 0; break;
        }
      }
    }

    this.x = wx;
    this.y = wy;
    this.angle = wAngle;

    return { x: wx, y: wy, angle: wAngle };
  }
}
