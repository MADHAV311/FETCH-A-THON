/**
 * TrafficFlow-MAPS: Frontend Configuration & Map Geometries
 */

export const MAPS_UI_CONFIG = {
  CANVAS_WIDTH: 1000,
  CANVAS_HEIGHT: 650,

  ORIGIN: { x: 80, y: 420, label: "Koramangala 4th Block" },
  DESTINATION: { x: 880, y: 140, label: "Electronic City Phase 1" },
  CENTRAL_JUNCTION: { x: 480, y: 320, label: "Central Arterial Junction" },
  DIVERSION_POINT: { x: 320, y: 380, label: "8th Cross Diversion" },

  DEFAULT_ROUTE: [
    { x: 80, y: 420 },
    { x: 220, y: 400 },
    { x: 320, y: 380 },
    { x: 480, y: 320 },
    { x: 680, y: 230 },
    { x: 880, y: 140 }
  ],

  BYPASS_ROUTE: [
    { x: 80, y: 420 },
    { x: 220, y: 400 },
    { x: 320, y: 380 },
    { x: 420, y: 520 },
    { x: 640, y: 490 },
    { x: 760, y: 340 },
    { x: 880, y: 140 }
  ],

  COLORS: {
    BG_DARK: "#080b11",
    ROAD_SURFACE: "#182030",
    ROAD_BORDER: "#2d3748",
    ROAD_MARKING: "#4a5568",
    DEFAULT_ROUTE_LINE: "#ef4444",
    BYPASS_ROUTE_LINE: "#10b981",
    CAR_BLUE: "#38bdf8",
    SIGNAL_RED: "#ef4444",
    SIGNAL_GREEN: "#10b981"
  }
};
