import { useMemo } from 'react';

/**
 * Animated SVG ring gauge for health score display.
 */
export default function HealthGauge({ score = 0, classification = 'Good', size = 180 }) {
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const fillPercent = score / 100;
  const dashOffset = circumference * (1 - fillPercent);

  const color = useMemo(() => {
    if (score >= 80) return 'var(--success)';
    if (score >= 60) return 'var(--info)';
    if (score >= 40) return 'var(--warning)';
    return 'var(--danger)';
  }, [score]);

  const glowColor = useMemo(() => {
    if (score >= 80) return 'rgba(52, 211, 153, 0.3)';
    if (score >= 60) return 'rgba(96, 165, 250, 0.3)';
    if (score >= 40) return 'rgba(251, 191, 36, 0.3)';
    return 'rgba(248, 113, 113, 0.3)';
  }, [score]);

  return (
    <div className="health-gauge-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <circle
          className="health-gauge-track"
          cx={size / 2}
          cy={size / 2}
          r={radius}
        />
        <circle
          className="health-gauge-fill"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          filter="url(#glow)"
          style={{ filter: `drop-shadow(0 0 8px ${glowColor})` }}
        />
      </svg>
      <div className="health-gauge-center">
        <span className="health-gauge-score" style={{ color }}>
          {Math.round(score)}
        </span>
        <span className="health-gauge-label" style={{ color }}>
          {classification}
        </span>
      </div>
    </div>
  );
}
