import { useRef, useEffect } from 'react';

/**
 * Canvas-based sparkline chart for inline metric visualization.
 * Draws a smooth filled area chart with gradient.
 */
export default function Sparkline({
  data = [],
  color = 'var(--accent)',
  height = 48,
  width,
  fillOpacity = 0.15,
  strokeWidth = 1.5,
  className = '',
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length < 2) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const w = width || rect.width;
    const h = height;

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;

    ctx.clearRect(0, 0, w, h);

    const max = Math.max(...data, 1);
    const min = Math.min(...data, 0);
    const range = max - min || 1;
    const padding = 2;

    const points = data.map((v, i) => ({
      x: (i / (data.length - 1)) * (w - padding * 2) + padding,
      y: h - padding - ((v - min) / range) * (h - padding * 2),
    }));

    // Resolve CSS variable to actual color
    const resolvedColor = getComputedColor(color, canvas);

    // Draw filled area
    ctx.beginPath();
    ctx.moveTo(points[0].x, h);
    for (const p of points) {
      ctx.lineTo(p.x, p.y);
    }
    ctx.lineTo(points[points.length - 1].x, h);
    ctx.closePath();

    const gradient = ctx.createLinearGradient(0, 0, 0, h);
    gradient.addColorStop(0, withAlpha(resolvedColor, fillOpacity));
    gradient.addColorStop(1, withAlpha(resolvedColor, 0));
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw line
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const cpx = (prev.x + curr.x) / 2;
      ctx.bezierCurveTo(cpx, prev.y, cpx, curr.y, curr.x, curr.y);
    }
    ctx.strokeStyle = resolvedColor;
    ctx.lineWidth = strokeWidth;
    ctx.stroke();

    // Draw endpoint dot
    const last = points[points.length - 1];
    ctx.beginPath();
    ctx.arc(last.x, last.y, 3, 0, Math.PI * 2);
    ctx.fillStyle = resolvedColor;
    ctx.fill();

  }, [data, color, height, width, fillOpacity, strokeWidth]);

  return (
    <canvas
      ref={canvasRef}
      className={`mini-sparkline ${className}`}
      style={{ width: width || '100%', height }}
    />
  );
}

function getComputedColor(cssVar, element) {
  if (cssVar.startsWith('var(')) {
    const varName = cssVar.slice(4, -1).trim();
    const computed = getComputedStyle(element).getPropertyValue(varName).trim();
    return computed || '#6C8EFF';
  }
  return cssVar;
}

function withAlpha(color, alpha) {
  // Handle hex
  if (color.startsWith('#')) {
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  // Handle rgb/rgba
  if (color.startsWith('rgb')) {
    const match = color.match(/[\d.]+/g);
    if (match && match.length >= 3) {
      return `rgba(${match[0]}, ${match[1]}, ${match[2]}, ${alpha})`;
    }
  }
  return color;
}
