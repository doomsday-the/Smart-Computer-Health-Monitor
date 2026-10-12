const STACK = [
  { icon: '⚛️',  name: 'React 18',            role: 'UI framework' },
  { icon: '⚡',  name: 'Vite',                role: 'Build tool & dev server' },
  { icon: '🔀',  name: 'React Router v6',     role: 'Client-side routing' },
  { icon: '🐍',  name: 'Python + psutil',      role: 'System monitoring core' },
  { icon: '🪟',  name: 'PySide6 (Qt6)',        role: 'Native desktop UI' },
  { icon: '🗄️', name: 'SQLite',              role: 'Historical data storage' },
  { icon: '📊',  name: 'ReportLab',           role: 'PDF report export' },
  { icon: '🚀',  name: 'Vercel',              role: 'Web deployment platform' },
];

const FEATURES = [
  'Real-time CPU, RAM, Disk, and Battery monitoring with per-core breakdown',
  'Deterministic health score engine (0–100) with explainable deductions',
  'Layered interpretation rules that detect critical, warning, and info events',
  'Smart recommendation engine with actionable, safe remediation steps',
  'Alert deduplication and persistence via SQLite',
  'Deep 500-snapshot history with time-series charts',
  'Live simulation scenarios (idle, normal, heavy, stress) for demo/testing',
  'PDF/CSV report export from the desktop application',
  'Dark-mode glassmorphism design system',
];

export default function AboutPage() {
  return (
    <div className="animate-in">
      {/* Hero */}
      <div className="card" style={{
        marginBottom: '16px',
        background: 'linear-gradient(135deg, var(--bg-elevated), var(--bg-glass))',
        textAlign: 'center',
        padding: '40px 24px',
      }}>
        <div style={{ fontSize: '48px', marginBottom: '12px' }}>🖥️</div>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 800,
          color: 'var(--text-primary)' }}>
          Smart Computer Health Monitor
        </h1>
        <p style={{ margin: '8px 0 0', fontSize: '14px', color: 'var(--text-secondary)',
          maxWidth: '520px', marginInline: 'auto', lineHeight: 1.7 }}>
          A full-stack system telemetry application that combines a Python-powered
          monitoring core with a modern React web dashboard and a native PySide6 desktop UI.
        </p>
        <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'center', gap: '10px' }}>
          <Badge label="v1.0.0" color="var(--accent)" />
          <Badge label="MIT Licence" color="var(--info)" />
          <Badge label="React + Python" color="var(--purple)" />
        </div>
      </div>

      {/* Features */}
      <div className="card" style={{ marginBottom: '16px' }}>
        <div className="card-header">
          <span className="card-title">Features</span>
        </div>
        <ul style={{ margin: 0, padding: '0 0 0 20px',
          display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {FEATURES.map((f, i) => (
            <li key={i} style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {f}
            </li>
          ))}
        </ul>
      </div>

      {/* Tech stack */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Technology Stack</span>
        </div>
        <div style={{ display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '10px' }}>
          {STACK.map(({ icon, name, role }) => (
            <div key={name} style={{
              padding: '12px 14px',
              background: 'var(--bg-input)',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}>
              <span style={{ fontSize: '20px' }}>{icon}</span>
              <div>
                <div style={{ fontWeight: 700, fontSize: '13px',
                  color: 'var(--text-primary)' }}>
                  {name}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '2px' }}>
                  {role}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Badge({ label, color }) {
  return (
    <span style={{
      padding: '4px 12px',
      borderRadius: 'var(--radius-pill)',
      background: `${color}22`,
      color,
      fontSize: '11px',
      fontWeight: 700,
      letterSpacing: '0.3px',
    }}>
      {label}
    </span>
  );
}
