/**
 * TrafficFlow-MAPS: Interactive Canvas Map Renderer (Google Maps Cyber-Dark)
 * High-visibility 2D rendering of roads, bottleneck queues, proactive bypass paths, and GPS vehicle tracking.
 */

import { MAPS_UI_CONFIG } from '../config.js';

export class MapRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.dpr = window.devicePixelRatio || 1;
    this.pulsePhase = 0;
    this.dashOffset = 0;

    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    this.dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * this.dpr;
    this.canvas.height = rect.height * this.dpr;
    this.scale = Math.min(this.canvas.width / 1000, this.canvas.height / 650);
  }

  render(state) {
    if (!state) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    this.pulsePhase += 0.05;
    this.dashOffset -= 1.2;

    ctx.save();
    ctx.clearRect(0, 0, w, h);

    // Apply scale & centering
    ctx.scale(this.scale, this.scale);

    // 1. Draw Map Background & City Blocks
    this.drawCityGrid(ctx);

    // 2. Draw Road Geometry
    this.drawRoadNetwork(ctx);

    // 3. Draw Route Overlays (Default Red route vs Bypass Green route)
    this.drawRoutePolylines(ctx, state);

    // 4. Draw Central Junction & Bottleneck Queue
    this.drawCentralJunction(ctx, state);

    // 5. Draw Diversion Point Marker (8th Cross)
    this.drawDiversionMarker(ctx, state);

    // 6. Draw Driver Vehicle
    this.drawDriverVehicle(ctx, state.vehicle);

    // 7. Draw Origin & Destination Pins
    this.drawOriginDestinationPins(ctx);

    ctx.restore();
  }

  drawCityGrid(ctx) {
    // Cyber dark gridlines
    ctx.strokeStyle = "rgba(30, 41, 59, 0.4)";
    ctx.lineWidth = 1;
    const step = 50;
    for (let x = 0; x < 1000; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, 650);
      ctx.stroke();
    }
    for (let y = 0; y < 650; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(1000, y);
      ctx.stroke();
    }

    // Stylized Building Blocks
    const buildings = [
      { x: 120, y: 150, w: 140, h: 180 },
      { x: 300, y: 120, w: 120, h: 160 },
      { x: 560, y: 80, w: 180, h: 110 },
      { x: 140, y: 470, w: 180, h: 140 },
      { x: 480, y: 400, w: 120, h: 80 },
      { x: 700, y: 390, w: 150, h: 180 }
    ];

    ctx.fillStyle = "rgba(15, 23, 42, 0.75)";
    ctx.strokeStyle = "rgba(51, 65, 85, 0.35)";
    ctx.lineWidth = 1.5;

    for (const b of buildings) {
      ctx.fillRect(b.x, b.y, b.w, b.h);
      ctx.strokeRect(b.x, b.y, b.w, b.h);
    }
  }

  drawRoadNetwork(ctx) {
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    // 1. Direct Arterial Road Base
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 36;
    ctx.beginPath();
    this.traceRoutePath(ctx, MAPS_UI_CONFIG.DEFAULT_ROUTE);
    ctx.stroke();

    // 2. Ring Bypass Road Base
    ctx.strokeStyle = "#162032";
    ctx.lineWidth = 32;
    ctx.beginPath();
    this.traceRoutePath(ctx, MAPS_UI_CONFIG.BYPASS_ROUTE);
    ctx.stroke();

    // Center Dashed Stripes
    ctx.strokeStyle = "rgba(148, 163, 184, 0.25)";
    ctx.lineWidth = 2;
    ctx.setLineDash([8, 8]);

    ctx.beginPath();
    this.traceRoutePath(ctx, MAPS_UI_CONFIG.DEFAULT_ROUTE);
    ctx.stroke();

    ctx.beginPath();
    this.traceRoutePath(ctx, MAPS_UI_CONFIG.BYPASS_ROUTE);
    ctx.stroke();

    ctx.setLineDash([]);
  }

  traceRoutePath(ctx, waypoints) {
    if (!waypoints || waypoints.length === 0) return;
    ctx.moveTo(waypoints[0].x, waypoints[0].y);
    for (let i = 1; i < waypoints.length; i++) {
      ctx.lineTo(waypoints[i].x, waypoints[i].y);
    }
  }

  drawRoutePolylines(ctx, state) {
    const isBypassActive = state.navigation.activeRouteId === "PROACTIVE_BYPASS";

    // Draw Default Congested Route Line
    ctx.save();
    ctx.lineWidth = 8;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    // Arterial line: starts blue, then turns GLOWING RED approaching the bottleneck
    const grad = ctx.createLinearGradient(80, 420, 480, 320);
    grad.addColorStop(0, "#38bdf8");
    grad.addColorStop(0.4, "#f59e0b");
    grad.addColorStop(0.7, "#ef4444");

    ctx.strokeStyle = isBypassActive ? "rgba(239, 68, 68, 0.25)" : grad;
    if (!isBypassActive) {
      ctx.shadowColor = "#ef4444";
      ctx.shadowBlur = 10;
    }
    ctx.beginPath();
    this.traceRoutePath(ctx, MAPS_UI_CONFIG.DEFAULT_ROUTE);
    ctx.stroke();
    ctx.restore();

    // Draw Proactive Green Wave Bypass Route Line
    ctx.save();
    ctx.lineWidth = isBypassActive ? 9 : 6;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    if (isBypassActive) {
      ctx.strokeStyle = "#10b981";
      ctx.shadowColor = "#10b981";
      ctx.shadowBlur = 14;
      ctx.setLineDash([12, 6]);
      ctx.lineDashOffset = this.dashOffset;
    } else {
      ctx.strokeStyle = "rgba(16, 185, 129, 0.45)";
      ctx.setLineDash([6, 6]);
    }

    ctx.beginPath();
    this.traceRoutePath(ctx, MAPS_UI_CONFIG.BYPASS_ROUTE);
    ctx.stroke();
    ctx.restore();
  }

  drawCentralJunction(ctx, state) {
    const jx = 480;
    const jy = 320;
    const qTailX = 320;
    const qTailY = 380;

    // 1. Highlight Exact Congestion Zone (350m Backlog Span between 8th Cross & Central Junction)
    ctx.save();
    ctx.strokeStyle = "rgba(239, 68, 68, 0.4)";
    ctx.lineWidth = 26;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(qTailX, qTailY);
    ctx.lineTo(jx, jy);
    ctx.stroke();

    // Animated Hazard Stripes along the exact bottleneck stretch
    ctx.strokeStyle = "rgba(254, 202, 202, 0.55)";
    ctx.lineWidth = 4;
    ctx.setLineDash([10, 10]);
    ctx.lineDashOffset = this.dashOffset;
    ctx.beginPath();
    ctx.moveTo(qTailX, qTailY);
    ctx.lineTo(jx, jy);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // 2. Exact Dimension Bracket & Span Callout
    const midX = (qTailX + jx) / 2;
    const midY = (qTailY + jy) / 2 - 24;

    ctx.save();
    // Glassmorphic Exact Bottleneck Badge
    ctx.fillStyle = "rgba(15, 23, 42, 0.92)";
    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = 1.5;
    ctx.shadowColor = "#ef4444";
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.roundRect(midX - 145, midY - 26, 290, 34, 6);
    ctx.fill();
    ctx.stroke();

    ctx.font = "bold 11px Inter, sans-serif";
    ctx.fillStyle = "#fca5a5";
    ctx.textAlign = "center";
    ctx.fillText("📍 EXACT BOTTLENECK: North Stopline (Pillar #412)", midX, midY - 12);
    ctx.font = "10px Inter, sans-serif";
    ctx.fillStyle = "#fde047";
    ctx.fillText("📏 350m Backlog Span to 8th Cross • Lanes 1 & 2 Blocked", midX, midY + 1);
    ctx.restore();

    // 3. Queue Tail Milestone Pin at (qTailX, qTailY)
    ctx.save();
    ctx.fillStyle = "#ef4444";
    ctx.beginPath();
    ctx.arc(qTailX + 15, qTailY - 6, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.font = "bold 9px Inter, sans-serif";
    ctx.fillStyle = "#fca5a5";
    ctx.textAlign = "left";
    ctx.fillText("◀ Queue Tail (350m back)", qTailX + 24, qTailY - 3);
    ctx.restore();

    // 4. Junction Box & Stopline at (jx, jy)
    ctx.save();
    // Stopline bar across road
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(jx - 18, jy - 14);
    ctx.lineTo(jx - 6, jy + 18);
    ctx.stroke();

    ctx.fillStyle = "rgba(30, 41, 59, 0.85)";
    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(jx, jy, 28, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Red Signal Light Halo
    const redGlow = 14 + Math.sin(this.pulsePhase * 3) * 4;
    ctx.fillStyle = "#ef4444";
    ctx.shadowColor = "#ef4444";
    ctx.shadowBlur = redGlow;
    ctx.beginPath();
    ctx.arc(jx, jy, 9, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // 5. Draw Simulated Queue of Cars (Red brake lights)
    const queueCars = state.junction ? state.junction.queue : 34;
    const visibleQueueCount = Math.min(10, Math.floor(queueCars / 3.5));

    for (let i = 1; i <= visibleQueueCount; i++) {
      const qx = jx - i * 16 - 8;
      const qy = jy + i * 5;

      ctx.save();
      ctx.fillStyle = "#334155";
      ctx.strokeStyle = "#475569";
      ctx.lineWidth = 1;
      ctx.fillRect(qx - 8, qy - 5, 16, 10);
      ctx.strokeRect(qx - 8, qy - 5, 16, 10);

      // Tail brake lights glowing red
      ctx.fillStyle = "#ef4444";
      ctx.shadowColor = "#ef4444";
      ctx.shadowBlur = 6;
      ctx.fillRect(qx - 8, qy - 4, 2, 3);
      ctx.fillRect(qx - 8, qy + 1, 2, 3);
      ctx.restore();
    }

    // Label: "CENTRAL JUNCTION (34 CARS)"
    ctx.font = "bold 11px Inter, sans-serif";
    ctx.fillStyle = "#fca5a5";
    ctx.textAlign = "center";
    ctx.fillText("⚠️ CENTRAL JUNCTION (RED 44s)", jx + 30, jy - 36);
    ctx.font = "10px Inter, sans-serif";
    ctx.fillStyle = "#cbd5e1";
    ctx.fillText("34 Cars Queued • 108 ALS Preemption", jx + 30, jy - 22);
  }

  drawDiversionMarker(ctx, state) {
    const div = MAPS_UI_CONFIG.DIVERSION_POINT;

    // Glowing Decision Horizon Circle
    ctx.save();
    const ringRadius = 24 + Math.sin(this.pulsePhase * 2) * 4;
    ctx.strokeStyle = state.navigation.alertTriggered ? "#f59e0b" : "rgba(56, 189, 248, 0.4)";
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.arc(div.x, div.y, ringRadius, 0, Math.PI * 2);
    ctx.stroke();

    // Branching Turn Arrow Indicator
    ctx.fillStyle = state.navigation.rerouteDecision === "ACCEPTED" ? "#10b981" : "#f59e0b";
    ctx.beginPath();
    ctx.arc(div.x, div.y, 8, 0, Math.PI * 2);
    ctx.fill();

    ctx.font = "bold 11px Inter, sans-serif";
    ctx.fillStyle = "#fde68a";
    ctx.textAlign = "center";
    ctx.fillText("🔀 8th Cross Diversion Point", div.x, div.y - 34);
    ctx.font = "10px Inter, sans-serif";
    ctx.fillStyle = "#94a3b8";
    ctx.fillText("Turn Right to Bypass Bottleneck", div.x, div.y - 20);
    ctx.restore();
  }

  drawDriverVehicle(ctx, veh) {
    if (!veh) return;

    ctx.save();
    ctx.translate(veh.x, veh.y);
    ctx.rotate(veh.headingAngle);

    // Pulsing GPS ripple wave
    const pulseRad = 18 + Math.sin(this.pulsePhase * 4) * 6;
    ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(0, 0, pulseRad, 0, Math.PI * 2);
    ctx.stroke();

    // Headlight Beam Cone
    ctx.fillStyle = "rgba(254, 240, 138, 0.15)";
    ctx.beginPath();
    ctx.moveTo(12, 0);
    ctx.lineTo(65, -18);
    ctx.lineTo(65, 18);
    ctx.closePath();
    ctx.fill();

    // Car Body (Metallic Cyber Cyan)
    ctx.fillStyle = "#0284c7";
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 1.5;
    ctx.shadowColor = "#38bdf8";
    ctx.shadowBlur = 8;

    ctx.beginPath();
    ctx.roundRect(-14, -8, 28, 16, 4);
    ctx.fill();
    ctx.stroke();

    // Windshield
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(-2, -6, 7, 12);

    ctx.restore();
  }

  drawOriginDestinationPins(ctx) {
    const o = MAPS_UI_CONFIG.ORIGIN;
    const d = MAPS_UI_CONFIG.DESTINATION;

    // Origin Pin (Blue)
    ctx.fillStyle = "#38bdf8";
    ctx.shadowColor = "#38bdf8";
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.arc(o.x, o.y, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.font = "bold 11px Inter, sans-serif";
    ctx.fillStyle = "#38bdf8";
    ctx.textAlign = "center";
    ctx.fillText("📍 Start: Koramangala", o.x, o.y + 22);

    // Destination Pin (Red)
    ctx.fillStyle = "#ef4444";
    ctx.shadowColor = "#ef4444";
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.arc(d.x, d.y, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.font = "bold 11px Inter, sans-serif";
    ctx.fillStyle = "#ef4444";
    ctx.fillText("🏁 Destination: Electronic City", d.x, d.y - 16);
  }
}
