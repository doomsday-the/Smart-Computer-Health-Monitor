import { useTelemetry } from '../context/TelemetryContext';
import HealthGauge from '../components/HealthGauge';
import Sparkline from '../components/Sparkline';

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

function formatRate(bytesPerSec) {
  return `${formatBytes(bytesPerSec)}/s`;
}

export default function OverviewPage() {
  const { reading, health, history, insights } = useTelemetry();

  if (!reading || !health) {
    return <div className="empty-state"><p>Initializing telemetry...</p></div>;
  }

  const activeInsights = insights.filter(i => i.severity === 'critical' || i.severity === 'warning');

  return (
    <div>
      <div className="stat-grid animate-in">
        <StatCard
          icon="⚡"
          iconClass="cpu"
          label="CPU"
          value={reading.cpu_percent.toFixed(1)}
          unit="%"
          detail={`${reading.cpu_cores_percent.length} cores @ ${reading.cpu_frequency_mhz} MHz`}
          sparkData={history.cpu}
          sparkColor={getResourceColor(reading.cpu_percent)}
        />
        <StatCard
          icon="🧠"
          iconClass="ram"
          label="Memory"
          value={reading.ram_percent.toFixed(1)}
          unit="%"
          detail={`${formatBytes(reading.ram_available_bytes)} available of ${formatBytes(reading.ram_total_bytes)}`}
          sparkData={history.ram}
          sparkColor={getResourceColor(reading.ram_percent)}
        />
        <StatCard
          icon="💾"
          iconClass="disk"
          label="Disk"
          value={reading.disk_percent.toFixed(1)}
          unit="%"
          detail={`${formatBytes(reading.disk_free_bytes)} free of ${formatBytes(reading.disk_total_bytes)}`}
          sparkData={history.disk}
          sparkColor={getResourceColor(reading.disk_percent, 75, 90)}
        />
        <StatCard
          icon="🔋"
          iconClass="battery"
          label="Battery"
          value={reading.battery_percent.toFixed(1)}
          unit="%"
          detail={reading.battery_plugged ? 'Plugged in' : `${reading.battery_secs_left ? Math.round(reading.battery_secs_left / 60) + ' min remaining' : 'On battery'}`}
        />
      </div>

      <div className="grid-2 animate-in animate-in-delay-1">
        {/* Health Score */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">System Health Score</span>
            <span className={`badge badge-${health.classification.toLowerCase()}`}>
              {health.classification}
            </span>
          </div>
          <div className="health-gauge-container">
            <HealthGauge score={health.score} classification={health.classification} />
            <div className="health-breakdown">
              <BreakdownItem label="CPU" value={health.breakdown.cpu_deduction} color="var(--accent)" />
              <BreakdownItem label="RAM" value={health.breakdown.ram_deduction} color="var(--purple)" />
              <BreakdownItem label="Disk" value={health.breakdown.disk_deduction} color="var(--warning)" />
              <BreakdownItem label="Battery" value={health.breakdown.battery_deduction} color="var(--success)" />
            </div>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', textAlign: 'center', marginTop: '8px', lineHeight: 1.6 }}>
            {health.explanation}
          </p>
        </div>

        {/* Active Alerts */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Active Alerts</span>
            <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
              {activeInsights.length} active
            </span>
          </div>
          {activeInsights.length === 0 ? (
            <div className="empty-state" style={{ padding: '32px 16px' }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              <h3>All Clear</h3>
              <p>No active warnings or critical alerts. System is operating within healthy parameters.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {activeInsights.slice(0, 4).map(ins => (
                <MiniInsight key={ins.id} insight={ins} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Disk I/O & Cores */}
      <div className="grid-2 animate-in animate-in-delay-2" style={{ marginTop: '16px' }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">Disk I/O Activity</span>
          </div>
          <div style={{ display: 'flex', gap: '24px' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Read</div>
              <div style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--info)' }}>
                {formatRate(reading.disk_read_bytes_sec)}
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Write</div>
              <div style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--warning)' }}>
                {formatRate(reading.disk_write_bytes_sec)}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">CPU Core Utilization</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
            {reading.cpu_cores_percent.map((pct, i) => (
              <CoreBar key={i} index={i} percent={pct} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, iconClass, label, value, unit, detail, sparkData, sparkColor }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${iconClass}`}>{icon}</div>
      <div className="stat-content">
        <div className="stat-label">{label}</div>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
          <div>
            <span className="stat-value">{value}</span>
            <span className="stat-unit">{unit}</span>
          </div>
          {sparkData && sparkData.length > 2 && (
            <div style={{ width: '80px', height: '32px' }}>
              <Sparkline data={sparkData} color={sparkColor} height={32} />
            </div>
          )}
        </div>
        {detail && <div className="stat-detail">{detail}</div>}
      </div>
    </div>
  );
}

function BreakdownItem({ label, value, color }) {
  return (
    <div className="breakdown-item">
      <span className="breakdown-dot" style={{ background: color }} />
      <span>{label}</span>
      <span style={{ fontFamily: 'var(--font-mono)', color: value > 0 ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>
        -{value}
      </span>
    </div>
  );
}

function CoreBar({ index, percent }) {
  const color = percent > 85 ? 'var(--danger)' : percent > 65 ? 'var(--warning)' : 'var(--accent)';
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', marginBottom: '4px' }}>C{index}</div>
      <div style={{
        height: '48px',
        background: 'var(--bg-input)',
        borderRadius: '4px',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: `${percent}%`,
          background: color,
          borderRadius: '4px',
          transition: 'height 0.8s cubic-bezier(0.16, 1, 0.3, 1), background-color 0.5s',
          opacity: 0.7,
        }} />
      </div>
      <div style={{
        fontSize: '10px',
        fontFamily: 'var(--font-mono)',
        color: 'var(--text-secondary)',
        marginTop: '4px',
      }}>
        {percent.toFixed(0)}%
      </div>
    </div>
  );
}

function MiniInsight({ insight }) {
  return (
    <div style={{
      padding: '12px 14px',
      background: 'var(--bg-elevated)',
      borderRadius: 'var(--radius-md)',
      borderLeft: `3px solid ${insight.severity === 'critical' ? 'var(--danger)' : 'var(--warning)'}`,
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px',
    }}>
      <span style={{
        fontSize: '14px',
        marginTop: '1px',
      }}>
        {insight.resource === 'CPU' ? '⚡' : insight.resource === 'RAM' ? '🧠' : insight.resource === 'Disk' ? '💾' : insight.resource === 'Battery' ? '🔋' : '⚠️'}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>
          {insight.title}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
          {insight.observed_value}
        </div>
      </div>
      <span className={`insight-severity ${insight.severity}`}>
        {insight.severity}
      </span>
    </div>
  );
}

function getResourceColor(value, warnAt = 65, critAt = 85) {
  if (value >= critAt) return 'var(--danger)';
  if (value >= warnAt) return 'var(--warning)';
  return 'var(--accent)';
}
