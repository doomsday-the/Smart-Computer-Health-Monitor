import { useTelemetry } from '../context/TelemetryContext';
import Sparkline from '../components/Sparkline';

const SCORE_COLOR = (s) => {
  if (s >= 80) return 'var(--success)';
  if (s >= 60) return 'var(--info)';
  if (s >= 40) return 'var(--warning)';
  return 'var(--danger)';
};

function fmt(ts) {
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return ts;
  }
}

export default function HistoryPage() {
  const { deepHistory } = useTelemetry();

  if (!deepHistory || deepHistory.length === 0) {
    return (
      <div className="empty-state" style={{ padding: '80px 16px' }}>
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none"
          stroke="var(--text-tertiary)" strokeWidth="1.5">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        <h3>Collecting History…</h3>
        <p>Data will appear here after a few seconds of monitoring.</p>
      </div>
    );
  }

  // Last 60 entries for chart display
  const recent    = deepHistory.slice(-60);
  const cpuData   = recent.map(e => e.cpu);
  const ramData   = recent.map(e => e.ram);
  const diskData  = recent.map(e => e.disk);
  const scoreData = recent.map(e => e.score ?? 0);

  // Table shows newest first
  const tableRows = [...deepHistory].reverse().slice(0, 100);

  return (
    <div className="animate-in">
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700,
          color: 'var(--text-primary)' }}>
          History
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--text-tertiary)' }}>
          Showing last {deepHistory.length} snapshots (up to 500 · ~12 min at 1.5 s interval).
        </p>
      </div>

      {/* Time-series sparkline charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
        gap: '14px', marginBottom: '20px' }}>
        <SparkCard title="CPU %" data={cpuData}   color="var(--accent)"   warn={65} crit={85} />
        <SparkCard title="RAM %" data={ramData}   color="var(--purple)"  warn={70} crit={90} />
        <SparkCard title="Disk %" data={diskData} color="var(--warning)" warn={75} crit={90} />
        <SparkCard title="Health Score" data={scoreData} color="var(--success)"
          warn={60} crit={40} invertThresholds />
      </div>

      {/* Data table */}
      <div className="card" style={{ overflow: 'auto', maxHeight: '55vh' }}>
        <table className="process-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>CPU %</th>
              <th>RAM %</th>
              <th>Disk %</th>
              <th>Battery %</th>
              <th>Health Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {tableRows.map((row, i) => (
              <tr key={i}>
                <td>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px',
                    color: 'var(--text-tertiary)' }}>
                    {fmt(row.timestamp)}
                  </span>
                </td>
                <td><MetricCell value={row.cpu}  warn={65} crit={85} /></td>
                <td><MetricCell value={row.ram}  warn={70} crit={90} /></td>
                <td><MetricCell value={row.disk} warn={75} crit={90} /></td>
                <td>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                    {row.battery != null ? `${row.battery.toFixed(1)}%` : '—'}
                  </span>
                </td>
                <td>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px',
                    fontWeight: 700, color: SCORE_COLOR(row.score) }}>
                    {row.score?.toFixed(1) ?? '—'}
                  </span>
                </td>
                <td>
                  <span className="badge" style={{
                    background: `${SCORE_COLOR(row.score)}22`,
                    color: SCORE_COLOR(row.score),
                    fontSize: '10px',
                  }}>
                    {row.classification ?? '—'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SparkCard({ title, data, color, warn, crit, invertThresholds = false }) {
  if (!data || data.length < 2) return null;
  const last = data[data.length - 1];
  const min  = Math.min(...data).toFixed(1);
  const max  = Math.max(...data).toFixed(1);
  const avg  = (data.reduce((a, b) => a + b, 0) / data.length).toFixed(1);

  let valueColor = color;
  if (!invertThresholds) {
    if (last >= crit) valueColor = 'var(--danger)';
    else if (last >= warn) valueColor = 'var(--warning)';
  } else {
    if (last <= crit) valueColor = 'var(--danger)';
    else if (last <= warn) valueColor = 'var(--warning)';
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between',
        alignItems: 'baseline', marginBottom: '8px' }}>
        <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-tertiary)',
          textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {title}
        </span>
        <span style={{ fontSize: '18px', fontWeight: 700,
          fontFamily: 'var(--font-mono)', color: valueColor }}>
          {last?.toFixed(1)}
        </span>
      </div>
      <Sparkline data={data} color={valueColor} height={50} />
      <div style={{ display: 'flex', justifyContent: 'space-between',
        marginTop: '8px' }}>
        {[['Min', min], ['Avg', avg], ['Max', max]].map(([lbl, val]) => (
          <div key={lbl} style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)',
              textTransform: 'uppercase' }}>{lbl}</div>
            <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)',
              color: 'var(--text-secondary)' }}>{val}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MetricCell({ value, warn, crit }) {
  const color = value >= crit ? 'var(--danger)'
    : value >= warn ? 'var(--warning)'
    : 'var(--text-secondary)';
  return (
    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color }}>
      {value?.toFixed(1)}%
    </span>
  );
}
