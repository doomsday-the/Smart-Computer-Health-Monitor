import { useTelemetry } from '../context/TelemetryContext';

const SEVERITY_COLORS = {
  critical: 'var(--danger)',
  warning:  'var(--warning)',
  info:     'var(--info)',
  ok:       'var(--success)',
};

const RESOURCE_ICONS = {
  CPU:     '⚡',
  RAM:     '🧠',
  Disk:    '💾',
  Battery: '🔋',
  System:  '🖥️',
};

export default function InsightsPage() {
  const { insights } = useTelemetry();

  const sorted = [...insights].sort((a, b) => {
    const rank = { critical: 0, warning: 1, info: 2, ok: 3 };
    return (rank[a.severity] ?? 4) - (rank[b.severity] ?? 4);
  });

  return (
    <div className="animate-in">
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Health Insights
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--text-tertiary)' }}>
          Real-time analysis of CPU, RAM, Disk, and Battery behaviour.
        </p>
      </div>

      {/* Summary badges */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {['critical', 'warning', 'info', 'ok'].map(sev => {
          const count = sorted.filter(i => i.severity === sev).length;
          return (
            <div key={sev} style={{
              padding: '6px 14px',
              borderRadius: 'var(--radius-pill)',
              background: 'var(--bg-elevated)',
              border: `1px solid ${SEVERITY_COLORS[sev]}44`,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%',
                background: SEVERITY_COLORS[sev], display: 'inline-block' }} />
              <span style={{ fontSize: '12px', fontWeight: 600,
                color: SEVERITY_COLORS[sev], textTransform: 'capitalize' }}>
                {sev}
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-tertiary)',
                fontFamily: 'var(--font-mono)' }}>
                {count}
              </span>
            </div>
          );
        })}
      </div>

      {/* Insight cards */}
      {sorted.length === 0 ? (
        <div className="empty-state" style={{ padding: '60px 16px' }}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none"
            stroke="var(--success)" strokeWidth="1.5">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          <h3>All Clear</h3>
          <p>No active insights. System is operating within healthy parameters.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {sorted.map(ins => (
            <InsightCard key={ins.id} insight={ins} />
          ))}
        </div>
      )}
    </div>
  );
}

function InsightCard({ insight }) {
  const color  = SEVERITY_COLORS[insight.severity] || 'var(--text-tertiary)';
  const icon   = RESOURCE_ICONS[insight.resource] || '⚠️';

  return (
    <div className="card" style={{
      borderLeft: `3px solid ${color}`,
      padding: '16px 20px',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
        <span style={{ fontSize: '22px', lineHeight: 1, marginTop: '2px' }}>{icon}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Title row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px',
            flexWrap: 'wrap', marginBottom: '6px' }}>
            <span style={{ fontWeight: 700, fontSize: '14px',
              color: 'var(--text-primary)' }}>
              {insight.title}
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
              {insight.severity}
            </span>
            <span style={{
              padding: '2px 8px',
              borderRadius: 'var(--radius-pill)',
              background: 'var(--bg-input)',
              color: 'var(--text-tertiary)',
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
            }}>
              {insight.resource}
            </span>
          </div>

          {/* Observed value */}
          {insight.observed_value && (
            <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)',
              color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Observed: {insight.observed_value}
            </div>
          )}

          {/* Explanation */}
          {insight.explanation && (
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)',
              lineHeight: 1.6 }}>
              {insight.explanation}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
