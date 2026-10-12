import { useState, useMemo } from 'react';
import { useTelemetry } from '../context/TelemetryContext';

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

export default function ProcessExplorerPage() {
  const { reading } = useTelemetry();
  const [sortKey, setSortKey] = useState('cpu_percent');
  const [sortDir, setSortDir] = useState('desc');
  const [filter, setFilter] = useState('');

  const processes = useMemo(() => {
    if (!reading?.processes) return [];
    let list = [...reading.processes];

    if (filter) {
      const lower = filter.toLowerCase();
      list = list.filter(p => p.name.toLowerCase().includes(lower) || String(p.pid).includes(lower));
    }

    list.sort((a, b) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      return sortDir === 'desc' ? bv - av : av - bv;
    });

    return list;
  }, [reading, sortKey, sortDir, filter]);

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const SortArrow = ({ column }) => {
    if (sortKey !== column) return null;
    return <span style={{ marginLeft: '4px' }}>{sortDir === 'desc' ? '↓' : '↑'}</span>;
  };

  if (!reading) {
    return <div className="empty-state"><p>Waiting for process data...</p></div>;
  }

  return (
    <div className="animate-in">
      <div className="card" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '200px' }}>
            <input
              type="text"
              placeholder="Filter processes by name or PID..."
              value={filter}
              onChange={e => setFilter(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px 10px 36px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)',
                fontSize: '12px',
                outline: 'none',
                transition: 'border-color 150ms',
              }}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border-default)'}
            />
            <svg
              width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="2"
              style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
            {processes.length} processes
          </span>
        </div>
      </div>

      <div className="card" style={{ overflow: 'auto', maxHeight: '65vh' }}>
        <table className="process-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('name')} className={sortKey === 'name' ? 'sorted' : ''}>
                Process <SortArrow column="name" />
              </th>
              <th onClick={() => handleSort('pid')} className={sortKey === 'pid' ? 'sorted' : ''}>
                PID <SortArrow column="pid" />
              </th>
              <th onClick={() => handleSort('cpu_percent')} className={sortKey === 'cpu_percent' ? 'sorted' : ''}>
                CPU % <SortArrow column="cpu_percent" />
              </th>
              <th onClick={() => handleSort('memory_used_bytes')} className={sortKey === 'memory_used_bytes' ? 'sorted' : ''}>
                Memory <SortArrow column="memory_used_bytes" />
              </th>
              <th onClick={() => handleSort('memory_percent')} className={sortKey === 'memory_percent' ? 'sorted' : ''}>
                Mem % <SortArrow column="memory_percent" />
              </th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {processes.map(p => (
              <tr key={`${p.name}-${p.pid}`}>
                <td>
                  <span className="process-name">{p.name}</span>
                </td>
                <td>
                  <span className="process-pid">{p.pid}</span>
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div className="progress-bar" style={{ width: '60px', height: '4px' }}>
                      <div className="progress-bar-fill" style={{
                        width: `${Math.min(p.cpu_percent, 100)}%`,
                        background: p.cpu_percent > 50 ? 'var(--danger)' : p.cpu_percent > 20 ? 'var(--warning)' : 'var(--accent)',
                      }} />
                    </div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                      {p.cpu_percent.toFixed(1)}%
                    </span>
                  </div>
                </td>
                <td>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                    {formatBytes(p.memory_used_bytes)}
                  </span>
                </td>
                <td>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                    {p.memory_percent.toFixed(1)}%
                  </span>
                </td>
                <td>
                  <span className="badge" style={{
                    background: 'var(--success-subtle)',
                    color: 'var(--success)',
                    fontSize: '10px',
                  }}>
                    {p.status}
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
