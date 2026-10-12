import { useTelemetry } from '../context/TelemetryContext';
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

export default function ResourceMonitorPage() {
  const { reading, history } = useTelemetry();

  if (!reading) {
    return <div className="empty-state"><p>Waiting for telemetry data...</p></div>;
  }

  return (
    <div>
      {/* CPU Section */}
      <div className="card resource-section animate-in">
        <div className="resource-header">
          <div className="resource-title">
            <span>⚡</span>
            Processor (CPU)
          </div>
          <div className="resource-value-lg" style={{ color: getColor(reading.cpu_percent) }}>
            {reading.cpu_percent.toFixed(1)}
            <span style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-tertiary)' }}>%</span>
          </div>
        </div>

        <Sparkline data={history.cpu} color={getColor(reading.cpu_percent)} height={80} />

        <div style={{ display: 'flex', gap: '32px', marginTop: '16px', flexWrap: 'wrap' }}>
          <MetricItem label="Frequency" value={`${reading.cpu_frequency_mhz} MHz`} />
          <MetricItem label="Cores" value={reading.cpu_cores_percent.length} />
          <MetricItem label="Min (window)" value={`${Math.min(...(history.cpu.length ? history.cpu : [0])).toFixed(1)}%`} />
          <MetricItem label="Max (window)" value={`${Math.max(...(history.cpu.length ? history.cpu : [0])).toFixed(1)}%`} />
          <MetricItem label="Avg (window)" value={`${history.cpu.length ? (history.cpu.reduce((a, b) => a + b, 0) / history.cpu.length).toFixed(1) : 0}%`} />
        </div>

        <div style={{ marginTop: '16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Per-Core Utilization
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {reading.cpu_cores_percent.map((pct, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)', width: '32px' }}>
                  Core {i}
                </span>
                <div className="progress-bar" style={{ flex: 1 }}>
                  <div
                    className="progress-bar-fill"
                    style={{
                      width: `${pct}%`,
                      background: getColor(pct),
                    }}
                  />
                </div>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', width: '40px', textAlign: 'right' }}>
                  {pct.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* RAM Section */}
      <div className="card resource-section animate-in animate-in-delay-1">
        <div className="resource-header">
          <div className="resource-title">
            <span>🧠</span>
            Memory (RAM)
          </div>
          <div className="resource-value-lg" style={{ color: getColor(reading.ram_percent, 70, 90) }}>
            {reading.ram_percent.toFixed(1)}
            <span style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-tertiary)' }}>%</span>
          </div>
        </div>

        <Sparkline data={history.ram} color={getColor(reading.ram_percent, 70, 90)} height={80} />

        <div style={{ display: 'flex', gap: '32px', marginTop: '16px', flexWrap: 'wrap' }}>
          <MetricItem label="Used" value={formatBytes(reading.ram_used_bytes)} />
          <MetricItem label="Available" value={formatBytes(reading.ram_available_bytes)} />
          <MetricItem label="Total" value={formatBytes(reading.ram_total_bytes)} />
        </div>

        <div style={{ marginTop: '14px' }}>
          <div className="progress-bar" style={{ height: '10px' }}>
            <div
              className="progress-bar-fill"
              style={{
                width: `${reading.ram_percent}%`,
                background: `linear-gradient(90deg, var(--purple), ${getColor(reading.ram_percent, 70, 90)})`,
              }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px' }}>
            <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>0%</span>
            <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>100%</span>
          </div>
        </div>
      </div>

      {/* Disk Section */}
      <div className="card resource-section animate-in animate-in-delay-2">
        <div className="resource-header">
          <div className="resource-title">
            <span>💾</span>
            Storage ({reading.disk_path})
          </div>
          <div className="resource-value-lg" style={{ color: getColor(reading.disk_percent, 75, 90) }}>
            {reading.disk_percent.toFixed(1)}
            <span style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-tertiary)' }}>%</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '32px', marginTop: '12px', flexWrap: 'wrap' }}>
          <MetricItem label="Used" value={formatBytes(reading.disk_used_bytes)} />
          <MetricItem label="Free" value={formatBytes(reading.disk_free_bytes)} />
          <MetricItem label="Total" value={formatBytes(reading.disk_total_bytes)} />
          <MetricItem label="Read Rate" value={formatRate(reading.disk_read_bytes_sec)} />
          <MetricItem label="Write Rate" value={formatRate(reading.disk_write_bytes_sec)} />
        </div>

        <div style={{ marginTop: '14px' }}>
          <div className="progress-bar" style={{ height: '10px' }}>
            <div
              className="progress-bar-fill"
              style={{
                width: `${reading.disk_percent}%`,
                background: `linear-gradient(90deg, var(--warning), ${getColor(reading.disk_percent, 75, 90)})`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Battery Section */}
      <div className="card resource-section animate-in animate-in-delay-3">
        <div className="resource-header">
          <div className="resource-title">
            <span>🔋</span>
            Battery
          </div>
          <div className="resource-value-lg" style={{ color: getBatteryColor(reading.battery_percent, reading.battery_plugged) }}>
            {reading.battery_percent.toFixed(1)}
            <span style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-tertiary)' }}>%</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '32px', marginTop: '12px', flexWrap: 'wrap' }}>
          <MetricItem label="Status" value={reading.battery_plugged ? '⚡ Charging' : '🔌 Discharging'} />
          {reading.battery_secs_left != null && (
            <MetricItem label="Time Left" value={`${Math.round(reading.battery_secs_left / 60)} min`} />
          )}
        </div>

        <div style={{ marginTop: '14px' }}>
          <div className="progress-bar" style={{ height: '10px' }}>
            <div
              className="progress-bar-fill"
              style={{
                width: `${reading.battery_percent}%`,
                background: getBatteryColor(reading.battery_percent, reading.battery_plugged),
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricItem({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {label}
      </div>
      <div style={{ fontSize: '14px', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', marginTop: '2px' }}>
        {value}
      </div>
    </div>
  );
}

function getColor(val, warn = 65, crit = 85) {
  if (val >= crit) return 'var(--danger)';
  if (val >= warn) return 'var(--warning)';
  return 'var(--accent)';
}

function getBatteryColor(pct, plugged) {
  if (plugged) return 'var(--success)';
  if (pct <= 10) return 'var(--danger)';
  if (pct <= 25) return 'var(--warning)';
  return 'var(--success)';
}
