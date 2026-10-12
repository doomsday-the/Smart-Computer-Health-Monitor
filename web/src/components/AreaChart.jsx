import { useRef, useEffect } from 'react';

/**
 * Full-width canvas area chart for the History page.
 * Draws multiple data series with gradient fills.
 */
export default function AreaChart({
  series = [],
  height = 280,
  labels = [],
  className = '',
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || series.length === 0) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const w = rect.width;
    const h = height;

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;

    ctx.clearRect(0, 0, w, h);

    const padTop = 10;
    const padBottom = 30;
    const padLeft = 45;
    const padRight = 10;
    const chartW = w - padLeft - padRight;
    const chartH = h - padTop - padBottom;

    // Draw grid lines
    ctx.strokeStyle = 'rgba(60, 80, 120, 0.15)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    for (let i = 0; i <= 4; i++) {
      const y = padTop + (chartH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(w - padRight, y);
      ctx.stroke();
    }
    ctx.setLineDash([]);

    // Y-axis labels
    ctx.font = '10px Inter, sans-serif';
    ctx.fillStyle = '#5A6478';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
      const y = padTop + (chartH / 4) * i;
      const val = 100 - (i * 25);
      ctx.fillText(`${val}%`, padLeft - 8, y + 3);
    }

    // X-axis time labels
    if (labels.length > 0) {
      ctx.textAlign = 'center';
      const step = Math.max(1, Math.floor(labels.length / 6));
      for (let i = 0; i < labels.length; i += step) {
        const x = padLeft + (i / Math.max(1, labels.length - 1)) * chartW;
        const time = new Date(labels[i]);
        const label = `${time.getHours().toString().padStart(2, '0')}:${time.getMinutes().toString().padStart(2, '0')}:${time.getSeconds().toString().padStart(2, '0')}`;
        ctx.fillText(label, x, h - 8);
      }
    }

    // Draw each series
    for (const { data, color, label } of series) {
      if (!data || data.length < 2) continue;

      const resolvedColor = resolveColor(color, canvas);
      const max = 100;
      const min = 0;
      const range = max - min || 1;

      const points = data.map((v, i) => ({
        x: padLeft + (i / (data.length - 1)) * chartW,
        y: padTop + chartH - ((v - min) / range) * chartH,
      }));

      // Filled area
      ctx.beginPath();
      ctx.moveTo(points[0].x, padTop + chartH);
      for (const p of points) ctx.lineTo(p.x, p.y);
      ctx.lineTo(points[points.length - 1].x, padTop + chartH);
      ctx.closePath();

      const gradient = ctx.createLinearGradient(0, padTop, 0, padTop + chartH);
      gradient.addColorStop(0, withAlpha(resolvedColor, 0.2));
      gradient.addColorStop(1, withAlpha(resolvedColor, 0));
      ctx.fillStyle = gradient;
      ctx.fill();

      // Line
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        const prev = points[i - 1];
        const curr = points[i];
        const cpx = (prev.x + curr.x) / 2;
        ctx.bezierCurveTo(cpx, prev.y, cpx, curr.y, curr.x, curr.y);
      }
      ctx.strokeStyle = resolvedColor;
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }, [series, height, labels]);

  return (
    <canvas
      ref={canvasRef}
      className={`area-chart ${className}`}
      style={{ width: '100%', height, display: 'block' }}
    />
  );
}

function resolveColor(cssVar, element) {
  if (cssVar.startsWith('var(')) {
    const varName = cssVar.slice(4, -1).trim();
    return getComputedStyle(element).getPropertyValue(varName).trim() || '#6C8EFF';
  }
  return cssVar;
}

function withAlpha(color, alpha) {
  if (color.startsWith('#')) {
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  if (color.startsWith('rgb')) {
    const match = color.match(/[\d.]+/g);
    if (match && match.length >= 3) {
      return `rgba(${match[0]}, ${match[1]}, ${match[2]}, ${alpha})`;
    }
  }
  return color;
}
