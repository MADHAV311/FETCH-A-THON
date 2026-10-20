/**
 * AI Adaptive Traffic Signal Digital Twin - High-Performance Canvas Chart Renderer
 * Renders real-time time-series telemetry charts for Wait Time, Queue Length, and Throughput comparisons.
 */

export class ChartRenderer {
  constructor() {
    this.dpr = window.devicePixelRatio || 1;
  }

  /**
   * Draws a dual-line time series chart comparing Fixed-Time vs AI Adaptive
   * @param {HTMLCanvasElement} canvas
   * @param {Array<number>} seriesFixed
   * @param {Array<number>} seriesAI
   * @param {Object} options
   */
  renderDualLineChart(canvas, seriesFixed, seriesAI, options = {}) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    if (canvas.width !== rect.width * this.dpr || canvas.height !== rect.height * this.dpr) {
      canvas.width = rect.width * this.dpr;
      canvas.height = rect.height * this.dpr;
    }

    const dpr = this.dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const w = rect.width;
    const h = rect.height;
    const padLeft = 32;
    const padBottom = 20;
    const padTop = 14;
    const padRight = 14;

    const plotW = w - padLeft - padRight;
    const plotH = h - padTop - padBottom;

    // Clear background
    ctx.fillStyle = '#0a0e1a';
    ctx.fillRect(0, 0, w, h);

    // Compute max value for scaling
    let maxVal = Math.max(
      10,
      options.minMax || 0,
      ...(seriesFixed.length ? seriesFixed : [0]),
      ...(seriesAI.length ? seriesAI : [0])
    );
    maxVal = Math.ceil(maxVal * 1.15);

    // Draw horizontal grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.lineWidth = 1;
    ctx.font = '9px monospace';
    ctx.fillStyle = '#64748b';
    ctx.textAlign = 'right';

    const gridSteps = 3;
    for (let i = 0; i <= gridSteps; i++) {
      const yVal = (maxVal / gridSteps) * i;
      const yPos = padTop + plotH - (i / gridSteps) * plotH;

      ctx.beginPath();
      ctx.moveTo(padLeft, yPos);
      ctx.lineTo(w - padRight, yPos);
      ctx.stroke();

      ctx.fillText(`${Math.round(yVal)}${options.unit || ''}`, padLeft - 6, yPos + 3);
    }

    const dataLen = Math.max(seriesFixed.length, seriesAI.length);
    if (dataLen < 2) {
      // Empty state hint
      ctx.fillStyle = '#475569';
      ctx.textAlign = 'center';
      ctx.font = '11px sans-serif';
      ctx.fillText('Accumulating simulation telemetry...', w / 2, h / 2);
      return;
    }

    // 1. Draw Fixed-Time Line (Blue)
    this.drawLine(ctx, seriesFixed, padLeft, padTop, plotW, plotH, maxVal, '#3b82f6', 'rgba(59, 130, 246, 0.15)');

    // 2. Draw AI Adaptive Line (Purple / Cyan)
    this.drawLine(ctx, seriesAI, padLeft, padTop, plotW, plotH, maxVal, '#a855f7', 'rgba(168, 85, 247, 0.2)');

    // 3. Current value indicators in top right
    const curFixed = seriesFixed.length ? seriesFixed[seriesFixed.length - 1] : 0;
    const curAI = seriesAI.length ? seriesAI[seriesAI.length - 1] : 0;

    ctx.font = 'bold 10px monospace';
    ctx.textAlign = 'right';

    ctx.fillStyle = '#60a5fa';
    ctx.fillText(`Fixed: ${Math.round(curFixed * 10) / 10}${options.unit || ''}`, w - padRight - 85, padTop - 2);

    ctx.fillStyle = '#c084fc';
    ctx.fillText(`AI: ${Math.round(curAI * 10) / 10}${options.unit || ''}`, w - padRight, padTop - 2);
  }

  /**
   * Helper to draw single line series with gradient area fill
   */
  drawLine(ctx, data, left, top, width, height, maxVal, strokeColor, fillColor) {
    if (data.length < 2) return;

    const count = data.length;
    const stepX = width / (count - 1);

    ctx.save();

    // Fill Area under curve
    ctx.beginPath();
    ctx.moveTo(left, top + height);

    for (let i = 0; i < count; i++) {
      const val = data[i];
      const x = left + i * stepX;
      const y = top + height - (val / maxVal) * height;
      if (i === 0) ctx.lineTo(x, y);
      else ctx.lineTo(x, y);
    }

    ctx.lineTo(left + width, top + height);
    ctx.closePath();
    ctx.fillStyle = fillColor;
    ctx.fill();

    // Draw Line stroke
    ctx.beginPath();
    for (let i = 0; i < count; i++) {
      const val = data[i];
      const x = left + i * stepX;
      const y = top + height - (val / maxVal) * height;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Last point dot
    const lastX = left + (count - 1) * stepX;
    const lastY = top + height - (data[count - 1] / maxVal) * height;
    ctx.fillStyle = strokeColor;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }
}
