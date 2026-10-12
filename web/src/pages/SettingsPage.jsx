import { useTelemetry } from '../context/TelemetryContext';

const SCENARIOS = [
  { key: 'auto',   label: 'Auto (cycles)',     desc: 'Automatic 3-minute cycle through all workload levels.' },
  { key: 'idle',   label: 'Idle',              desc: 'Low CPU (8-25%), RAM (35-50%). System at rest.' },
  { key: 'normal', label: 'Normal Workload',   desc: 'Moderate CPU (15-45%), RAM (45-65%). Everyday usage.' },
  { key: 'heavy',  label: 'Heavy Workload',    desc: 'High CPU (60-92%), RAM (70-90%). Compilation or gaming.' },
  { key: 'stress', label: 'Critical Stress',   desc: 'Max CPU (85-99%), RAM (88-97%). Near-threshold scenario.' },
];

export default function SettingsPage() {
  const { scenario, changeScenario, isLive, toggleLive, alertCount } = useTelemetry();

  return (
    <div className="animate-in">
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700,
          color: 'var(--text-primary)' }}>
          Settings
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--text-tertiary)' }}>
          Control the monitoring feed and simulation scenario.
        </p>
      </div>

      {/* Live / Pause toggle */}
      <div className="card" style={{ marginBottom: '16px' }}>
        <div className="card-header">
          <span className="card-title">Monitoring Feed</span>
          <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
            {alertCount > 0 ? `${alertCount} active alert${alertCount > 1 ? 's' : ''}` : 'No alerts'}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginTop: '4px' }}>
          <div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              {isLive
                ? '🟢 Live — telemetry polling every 1.5 s'
                : '⏸ Paused — snapshot frozen at last reading'}
            </div>
          </div>
          <button
            onClick={toggleLive}
            style={{
              marginLeft: 'auto',
              padding: '8px 22px',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              fontWeight: 600,
              fontSize: '13px',
              background: isLive ? 'var(--danger)' : 'var(--success)',
              color: '#fff',
              transition: 'background 200ms',
            }}
          >
            {isLive ? 'Pause' : 'Resume'}
          </button>
        </div>
      </div>

      {/* Scenario selector */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Simulation Scenario</span>
          <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
            Active: <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{scenario}</span>
          </span>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', margin: '0 0 16px' }}>
          Switch between workload profiles to test how the dashboard responds at different
          resource pressure levels.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {SCENARIOS.map(sc => {
            const active = scenario === sc.key;
            return (
              <button
                key={sc.key}
                onClick={() => changeScenario(sc.key)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  padding: '14px 18px',
                  borderRadius: 'var(--radius-md)',
                  border: `1.5px solid ${active ? 'var(--accent)' : 'var(--border-default)'}`,
                  background: active ? 'var(--accent-subtle)' : 'var(--bg-input)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'border-color 150ms, background 150ms',
                }}
              >
                <div style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  flexShrink: 0,
                  background: active ? 'var(--accent)' : 'var(--border-subtle)',
                  boxShadow: active ? '0 0 6px var(--accent)' : 'none',
                  transition: 'background 200ms, box-shadow 200ms',
                }} />
                <div>
                  <div style={{ fontWeight: 700, fontSize: '13px',
                    color: active ? 'var(--accent)' : 'var(--text-primary)' }}>
                    {sc.label}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '2px' }}>
                    {sc.desc}
                  </div>
                </div>
                {active && (
                  <svg style={{ marginLeft: 'auto', flexShrink: 0 }}
                    width="16" height="16" viewBox="0 0 24 24" fill="none"
                    stroke="var(--accent)" strokeWidth="2.5">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Poll interval info */}
      <div className="card" style={{ marginTop: '16px' }}>
        <div className="card-header">
          <span className="card-title">Poll Interval</span>
        </div>
        <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>
          Telemetry is refreshed every{' '}
          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>1500 ms</span>
          . This value is set in <code style={{ fontFamily: 'var(--font-mono)',
            fontSize: '12px', color: 'var(--text-secondary)' }}>TelemetryContext.jsx</code> and
          can be lowered for more frequent updates or raised to reduce CPU usage.
        </p>
      </div>
    </div>
  );
}
