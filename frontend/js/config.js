/**
 * AI Adaptive Traffic Signal Digital Twin - Global Configuration
 */

export const SIM_CONFIG = {
  // Intersection physical dimensions (in world coordinates / pixels)
  ROAD_WIDTH: 140,            // Total road width (70px per direction = 2 lanes * 35px)
  LANE_WIDTH: 35,             // 35px per lane
  LANES_PER_DIR: 2,           // 2 inbound lanes, 2 outbound lanes
  INTERSECTION_SIZE: 140,     // Central conflict box is 140x140
  STOP_LINE_OFFSET: 75,       // Distance from center to stop line
  SENSOR_LOOP_OFFSET: 130,    // Detection loop distance from center
  SENSOR_LOOP_LENGTH: 40,     // Loop detector length
  SPAWN_OFFSET: 480,          // Spawn point distance from center

  // Physics & Kinematics
  MAX_SPEED: 110,             // Max free-flow speed (pixels / sec)
  ACCELERATION: 85,           // Normal acceleration (px/s^2)
  DECELERATION: 110,          // Normal comfortable braking (px/s^2)
  HARD_BRAKING: 220,          // Emergency / stop-line braking (px/s^2)
  STANDSTILL_GAP: 12,         // Bumper-to-bumper standstill gap (px)
  TIME_HEADWAY: 1.2,          // Desired time gap to lead vehicle (sec)
  YELLOW_DECEL_DISTANCE: 140, // Distance within which a car can decide to pass yellow

  // Signal States
  SIGNAL_STATES: {
    RED: 'RED',
    YELLOW: 'YELLOW',
    GREEN: 'GREEN',
    ALL_RED: 'ALL_RED'
  },

  // Roads definition (A: North, B: East, C: South, D: West)
  ROADS: {
    NORTH: { id: 'A', name: 'Road A (North)', dir: 'N', angle: Math.PI / 2, approachFrom: 'N' },
    EAST:  { id: 'B', name: 'Road B (East)',  dir: 'E', angle: Math.PI,     approachFrom: 'E' },
    SOUTH: { id: 'C', name: 'Road C (South)', dir: 'S', angle: -Math.PI / 2, approachFrom: 'S' },
    WEST:  { id: 'D', name: 'Road D (West)',  dir: 'W', angle: 0,           approachFrom: 'W' }
  },

  // Road Order in cycle
  CYCLE_ORDER: ['A', 'B', 'C', 'D'],

  // Default Fixed-Time Controller Parameters
  FIXED_TIME_DEFAULTS: {
    greenDuration: {
      A: 30, // 30 sec
      B: 30, // 30 sec
      C: 30, // 30 sec
      D: 30  // 30 sec
    },
    yellowDuration: 3.5,  // 3.5 sec
    allRedDuration: 1.5   // 1.5 sec clearance
  },

  // Default AI Adaptive Controller Parameters
  ADAPTIVE_AI_DEFAULTS: {
    minGreen: 7.0,          // Minimum green duration (sec)
    maxGreen: 45.0,         // Maximum green duration (sec)
    yellowDuration: 3.5,    // Yellow duration (sec)
    allRedDuration: 1.5,    // All-red clearance (sec)
    saturationHeadway: 1.8, // Saturation discharge headway (sec / veh)
    startupLostTime: 2.5,   // Green start-up lost time (sec)
    gapOutThreshold: 2.2,   // Gap-out time without car to end green early (sec)
    weights: {
      queueLength: 1.2,     // Priority weight for waiting queue count
      maxWaitTime: 1.5,     // Priority weight for longest waiting vehicle
      totalWaitTime: 0.6,   // Priority weight for accumulated wait time
      arrivalRate: 0.4,     // Priority weight for incoming flow
      starvationMultiplier: 2.0 // Boost factor for roads waiting multiple cycles
    },
    starvationThresholdSec: 50.0 // Max wait before emergency priority boost
  },

  // Vehicle Types & Visual Configurations
  VEHICLE_TYPES: {
    SEDAN: {
      type: 'SEDAN',
      name: 'Sedan',
      length: 28,
      width: 14,
      maxSpeed: 115,
      accel: 90,
      decel: 120,
      weight: 0.50, // 50% chance
      colors: ['#38bdf8', '#0ea5e9', '#e2e8f0', '#94a3b8', '#3b82f6', '#475569']
    },
    SUV: {
      type: 'SUV',
      name: 'SUV',
      length: 32,
      width: 16,
      maxSpeed: 105,
      accel: 80,
      decel: 110,
      weight: 0.25, // 25% chance
      colors: ['#059669', '#10b981', '#1e293b', '#64748b', '#0d9488']
    },
    BUS: {
      type: 'BUS',
      name: 'City Bus',
      length: 50,
      width: 17,
      maxSpeed: 85,
      accel: 55,
      decel: 90,
      weight: 0.10, // 10% chance
      colors: ['#f59e0b', '#d97706', '#fbbf24']
    },
    TRUCK: {
      type: 'TRUCK',
      name: 'Delivery Truck',
      length: 44,
      width: 17,
      maxSpeed: 80,
      accel: 50,
      decel: 85,
      weight: 0.10, // 10% chance
      colors: ['#e11d48', '#be123c', '#cbd5e1']
    },
    SPORTS: {
      type: 'SPORTS',
      name: 'Sports Car',
      length: 26,
      width: 14,
      maxSpeed: 135,
      accel: 120,
      decel: 140,
      weight: 0.04, // 4% chance
      colors: ['#ec4899', '#f43f5e', '#8b5cf6']
    },
    EMERGENCY: {
      type: 'EMERGENCY',
      name: 'Ambulance / Emergency',
      length: 36,
      width: 16,
      maxSpeed: 130,
      accel: 110,
      decel: 130,
      weight: 0.01, // 1% random chance or manual button
      isEmergency: true,
      colors: ['#ffffff']
    }
  },

  // Built-in Traffic Presets (Arrival rate in vehicles / minute per road)
  PRESETS: {
    LOW: {
      name: 'Low Traffic',
      description: 'Sparse traffic with minimal queues',
      rates: { A: 5, B: 3, C: 4, D: 2 }
    },
    BALANCED: {
      name: 'Balanced Traffic',
      description: 'Equal medium density across all directions',
      rates: { A: 18, B: 18, C: 18, D: 18 }
    },
    HEAVY: {
      name: 'Heavy Traffic',
      description: 'High congestion stress test on all approaches',
      rates: { A: 38, B: 36, C: 38, D: 35 }
    },
    UNEVEN: {
      name: 'Uneven Traffic',
      description: 'Asymmetric distribution where Road A dominates',
      rates: { A: 50, B: 10, C: 5, D: 20 }
    },
    RUSH_HOUR: {
      name: 'Rush Hour Dynamic',
      description: 'Dynamically shifts heavy flow across roads over time',
      dynamic: true,
      phases: [
        { durationSec: 40, label: 'Phase 1: Morning Inbound (North heavy)', rates: { A: 52, B: 8, C: 6, D: 14 } },
        { durationSec: 40, label: 'Phase 2: Commercial Cross-Flow (West & East heavy)', rates: { A: 12, B: 48, C: 10, D: 44 } },
        { durationSec: 40, label: 'Phase 3: Evening Outbound (South heavy)', rates: { A: 8, B: 14, C: 54, D: 16 } },
        { durationSec: 40, label: 'Phase 4: Mixed Evening Congestion', rates: { A: 32, B: 36, C: 28, D: 34 } }
      ]
    }
  },

  // Environmental Impact Factors
  ENVIRONMENTAL: {
    IDLE_FUEL_LITER_PER_HOUR: 1.2,    // Liters burned idling per vehicle-hour
    IDLE_CO2_KG_PER_LITER: 2.31       // kg CO2 emitted per liter of fuel
  }
};
