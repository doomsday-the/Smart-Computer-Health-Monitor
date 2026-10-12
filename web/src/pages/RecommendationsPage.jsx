import { useState } from 'react';
import { useTelemetry } from '../context/TelemetryContext';

const PRIORITY_COLORS = {
  High:   'var(--danger)',
  Medium: 'var(--warning)',
  Low:    'var(--info)',
};

const RESOURCE_ICONS = {
  CPU:     '⚡',
  RAM:     '🧠',
  Disk:    '💾',
  Battery: '🔋',
  System:  '🖥️',
};

export default function RecommendationsPage() {
  const { recommendations } = useTelemetry();
  const [expanded, setExpanded] = useState(null);

  const toggle = (id) => setExpanded(prev => (prev === id ? null : id));

  return (
    <div className="animate-in">
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700,
          color: 'var(--text-primary)' }}>
          Recommendations
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--text-tertiary)' }}>
          Actionable, safe steps to improve system performance.
        </p>
      </div>

      {recommendations.length === 0 ? (
        <div className="empty-state" style={{ padding: '60px 16px' }}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none"
            stroke="var(--success)" strokeWidth="1.5">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          <h3>No Recommendations</h3>
          <p>System is running smoothly. No actions required at this time.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {recommendations.map((rec) => (
            <RecommendationCard
              key={rec.id}
              rec={rec}
              isOpen={expanded === rec.id}
              onToggle={() => toggle(rec.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function RecommendationCard({ rec, isOpen, onToggle }) {
  const color = PRIORITY_COLORS[rec.priority] || 'var(--text-tertiary)';
  const icon  = RESOURCE_ICONS[rec.related_resource] || '⚠️';

  return (
    <div className="card" style={{ borderLeft: `3px solid ${color}`, padding: 0, overflow: 'hidden' }}>
      {/* Clickable header */}
      <button
        onClick={onToggle}
        style={{
          width: '100%',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '14px',
          textAlign: 'left',
        }}
      >
        <span style={{ fontSize: '22px', lineHeight: 1 }}>{icon}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
              {rec.title}
            </span>
            <span style={{
              padding: '2px 8px',
              borderRadius: 'var(--radius-pill)',
              background: `${color}22`,
              color,
              fontSize: '10px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}>
              {rec.priority} Priority
            </span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
            {rec.reason}
          </div>
        </div>
        <svg
          width="16" height="16" viewBox="0 0 24 24" fill="none"
          stroke="var(--text-tertiary)" strokeWidth="2"
          style={{ flexShrink: 0, transition: 'transform 200ms',
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Expanded body */}
      {isOpen && (
        <div style={{ padding: '0 20px 18px 20px', borderTop: '1px solid var(--border-subtle)' }}>
          {/* Suggested Steps */}
          <div style={{ marginTop: '14px' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-tertiary)',
              textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '10px' }}>
              Suggested Steps
            </div>
            <ol style={{ margin: 0, paddingLeft: '20px', display: 'flex',
              flexDirection: 'column', gap: '6px' }}>
              {rec.suggested_steps.map((step, i) => (
                <li key={i} style={{ fontSize: '13px', color: 'var(--text-secondary)',
                  lineHeight: 1.6 }}>
                  {step}
                </li>
              ))}
            </ol>
          </div>

          {/* Expected Benefit */}
          <div style={{ marginTop: '14px', padding: '10px 14px',
            background: 'var(--success-subtle)', borderRadius: 'var(--radius-md)' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--success)',
              textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Expected Benefit ·&nbsp;
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {rec.expected_benefit}
            </span>
          </div>

          {/* Safety Note */}
          {rec.safety_note && (
            <div style={{ marginTop: '8px', padding: '10px 14px',
              background: 'var(--warning-subtle)', borderRadius: 'var(--radius-md)' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--warning)',
                textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                ⚠ Safety Note ·&nbsp;
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {rec.safety_note}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
