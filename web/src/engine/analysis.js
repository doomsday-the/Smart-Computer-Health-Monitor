/**
 * Health Score Calculator
 * 
 * Port of the Python HealthScoreCalculator.
 * Deterministic 0-100 health score with breakdown and classification.
 */

const DEFAULT_THRESHOLDS = {
  cpu_warning: 65,
  cpu_critical: 85,
  ram_warning: 70,
  ram_critical: 90,
  disk_warning: 75,
  disk_critical: 90,
  battery_warning: 25,
  battery_critical: 10,
};

export function calculateHealthScore(reading, thresholds = DEFAULT_THRESHOLDS) {
  const breakdown = {
    cpu_deduction: 0,
    ram_deduction: 0,
    disk_deduction: 0,
    battery_deduction: 0,
  };
  const reasons = [];

  // CPU deduction (up to 35)
  const cpu = reading.cpu_percent;
  if (cpu >= thresholds.cpu_critical) {
    const excess = (cpu - thresholds.cpu_critical) / Math.max(1, 100 - thresholds.cpu_critical);
    breakdown.cpu_deduction = 18 + 17 * Math.min(1, excess);
    reasons.push(`High CPU utilization (${cpu.toFixed(1)}%)`);
  } else if (cpu >= thresholds.cpu_warning) {
    const ratio = (cpu - thresholds.cpu_warning) / Math.max(1, thresholds.cpu_critical - thresholds.cpu_warning);
    breakdown.cpu_deduction = 5 + 13 * Math.min(1, ratio);
    reasons.push(`Elevated CPU usage (${cpu.toFixed(1)}%)`);
  }

  // RAM deduction (up to 35)
  const ram = reading.ram_percent;
  if (ram >= thresholds.ram_critical) {
    const excess = (ram - thresholds.ram_critical) / Math.max(1, 100 - thresholds.ram_critical);
    breakdown.ram_deduction = 18 + 17 * Math.min(1, excess);
    reasons.push(`High RAM pressure (${ram.toFixed(1)}%)`);
  } else if (ram >= thresholds.ram_warning) {
    const ratio = (ram - thresholds.ram_warning) / Math.max(1, thresholds.ram_critical - thresholds.ram_warning);
    breakdown.ram_deduction = 5 + 13 * Math.min(1, ratio);
    reasons.push(`Elevated RAM usage (${ram.toFixed(1)}%)`);
  }

  // Disk deduction (up to 20)
  const disk = reading.disk_percent;
  if (disk >= thresholds.disk_critical) {
    const excess = (disk - thresholds.disk_critical) / Math.max(1, 100 - thresholds.disk_critical);
    breakdown.disk_deduction = 12 + 8 * Math.min(1, excess);
    reasons.push(`Low free disk capacity (${disk.toFixed(1)}% used)`);
  } else if (disk >= thresholds.disk_warning) {
    const ratio = (disk - thresholds.disk_warning) / Math.max(1, thresholds.disk_critical - thresholds.disk_warning);
    breakdown.disk_deduction = 4 + 8 * Math.min(1, ratio);
    reasons.push(`Disk storage warning (${disk.toFixed(1)}% used)`);
  }

  // Battery deduction (up to 10) — only if discharging
  if (reading.battery_available && reading.battery_percent != null && !reading.battery_plugged) {
    const batt = reading.battery_percent;
    if (batt <= thresholds.battery_critical) {
      breakdown.battery_deduction = 10;
      reasons.push(`Battery critically low (${batt.toFixed(1)}%)`);
    } else if (batt <= thresholds.battery_warning) {
      const ratio = (thresholds.battery_warning - batt) / Math.max(1, thresholds.battery_warning - thresholds.battery_critical);
      breakdown.battery_deduction = 3 + 4 * Math.min(1, ratio);
      reasons.push(`Battery low (${batt.toFixed(1)}%)`);
    }
  }

  // Correlation damper
  let totalDeduction = Object.values(breakdown).reduce((a, b) => a + b, 0);
  if (breakdown.cpu_deduction > 10 && breakdown.ram_deduction > 10) {
    totalDeduction *= 0.85;
  }

  const score = Math.max(0, Math.min(100, 100 - totalDeduction));

  let classification, explanation;
  if (score >= 80) {
    classification = 'Excellent';
    explanation = reasons.length
      ? `Overall healthy with minor notice: ${reasons.join(', ')}.`
      : 'System resources are operating efficiently within healthy parameters.';
  } else if (score >= 60) {
    classification = 'Good';
    explanation = `Moderate load detected: ${reasons.join(', ')}.`;
  } else if (score >= 40) {
    classification = 'Warning';
    explanation = `Substantial resource strain: ${reasons.join(', ')}. Investigation recommended.`;
  } else {
    classification = 'Critical';
    explanation = `Critical performance pressure: ${reasons.join(', ')}. Immediate attention advised.`;
  }

  return {
    score: Math.round(score * 10) / 10,
    classification,
    explanation,
    breakdown: Object.fromEntries(
      Object.entries(breakdown).map(([k, v]) => [k, Math.round(v * 10) / 10])
    ),
  };
}

/**
 * Interpretation Engine (simplified JS port)
 * Generates structured insights from readings.
 */
export function generateInsights(reading, thresholds = DEFAULT_THRESHOLDS) {
  const insights = [];
  const now = new Date().toISOString();

  // CPU insight
  if (reading.cpu_percent >= thresholds.cpu_warning) {
    const severity = reading.cpu_percent >= thresholds.cpu_critical ? 'critical' : 'warning';
    const topCpu = (reading.processes || [])
      .sort((a, b) => b.cpu_percent - a.cpu_percent)
      .slice(0, 3);

    insights.push({
      id: 'cpu_sustained_pressure',
      resource: 'CPU',
      severity,
      title: severity === 'critical' ? 'Sustained High CPU Utilization' : 'Elevated CPU Load',
      observed_value: `${reading.cpu_percent.toFixed(1)}%`,
      explanation: `Processor utilization is at ${reading.cpu_percent.toFixed(1)}%. When CPU demand is high, thread scheduling queues grow, causing input latency and reduced application responsiveness.`,
      possible_cause: topCpu.length
        ? `Top consumers: ${topCpu.map(p => `${p.name} (${p.cpu_percent}%)`).join(', ')}`
        : 'Multiple background processes competing for CPU cycles.',
      recommendation: 'Review high-CPU processes in Process Explorer. Close unneeded background applications.',
      confidence: 'High Confidence (Direct Metric)',
      status: 'active',
      timestamp: now,
      evidence: {
        current_cpu: reading.cpu_percent,
        threshold: severity === 'critical' ? thresholds.cpu_critical : thresholds.cpu_warning,
        top_processes: topCpu.map(p => ({ name: p.name, pid: p.pid, cpu: p.cpu_percent })),
      },
    });
  }

  // RAM insight
  if (reading.ram_percent >= thresholds.ram_warning) {
    const severity = reading.ram_percent >= thresholds.ram_critical ? 'critical' : 'warning';
    const availMb = Math.round(reading.ram_available_bytes / 1024 / 1024);
    const totalMb = Math.round(reading.ram_total_bytes / 1024 / 1024);
    const topMem = (reading.processes || [])
      .sort((a, b) => b.memory_used_bytes - a.memory_used_bytes)
      .slice(0, 3);

    insights.push({
      id: 'ram_memory_pressure',
      resource: 'RAM',
      severity,
      title: severity === 'critical' ? 'High Memory Pressure' : 'Elevated Memory Consumption',
      observed_value: `${reading.ram_percent.toFixed(1)}% (${availMb} MB free)`,
      explanation: `RAM utilization at ${reading.ram_percent.toFixed(1)}%, leaving ${availMb} MB available of ${totalMb} MB. When physical RAM is exhausted, the OS pages memory to disk swap, degrading responsiveness.`,
      possible_cause: topMem.length
        ? `Heavy consumers: ${topMem.map(p => `${p.name} (${Math.round(p.memory_used_bytes / 1024 / 1024)} MB)`).join(', ')}`
        : 'Large working sets from open applications.',
      recommendation: 'Close memory-intensive browser tabs, IDEs, or background services not currently in use.',
      confidence: 'High Confidence (Direct Metric)',
      status: 'active',
      timestamp: now,
      evidence: {
        ram_percent: reading.ram_percent,
        available_mb: availMb,
        total_mb: totalMb,
        top_processes: topMem.map(p => ({ name: p.name, pid: p.pid, mem_mb: Math.round(p.memory_used_bytes / 1024 / 1024) })),
      },
    });
  }

  // Disk insight
  if (reading.disk_percent >= thresholds.disk_warning) {
    const severity = reading.disk_percent >= thresholds.disk_critical ? 'critical' : 'warning';
    const freeGb = (reading.disk_free_bytes / 1024 / 1024 / 1024).toFixed(1);
    const totalGb = (reading.disk_total_bytes / 1024 / 1024 / 1024).toFixed(1);

    insights.push({
      id: 'disk_storage_capacity',
      resource: 'Disk',
      severity,
      title: severity === 'critical' ? 'Critical Storage Exhaustion' : 'Low Disk Storage Warning',
      observed_value: `${reading.disk_percent.toFixed(1)}% (${freeGb} GB free)`,
      explanation: `Storage volume (${reading.disk_path}) is ${reading.disk_percent.toFixed(1)}% full with only ${freeGb} GB remaining. OS requires free space for temp files, paging, and updates.`,
      possible_cause: 'Accumulated caches, downloads, system logs, or large media files.',
      recommendation: 'Run Disk Cleanup. Inspect Downloads and temp folders. Empty Recycle Bin.',
      confidence: 'High Confidence (Direct Measurement)',
      status: 'active',
      timestamp: now,
      evidence: {
        disk_percent: reading.disk_percent,
        free_gb: parseFloat(freeGb),
        total_gb: parseFloat(totalGb),
        mount: reading.disk_path,
      },
    });
  }

  // Battery insight
  if (reading.battery_available && !reading.battery_plugged && reading.battery_percent <= thresholds.battery_warning) {
    const severity = reading.battery_percent <= thresholds.battery_critical ? 'critical' : 'warning';

    insights.push({
      id: 'battery_charge_depletion',
      resource: 'Battery',
      severity,
      title: severity === 'critical' ? 'Critically Low Battery' : 'Low Battery Charge',
      observed_value: `${reading.battery_percent.toFixed(1)}% (unplugged)`,
      explanation: `Battery at ${reading.battery_percent.toFixed(1)}% while on battery power. OS may trigger emergency hibernation if charge depletes.`,
      possible_cause: 'Device disconnected from AC power with active workload draining the battery.',
      recommendation: 'Connect AC power immediately. Save work and enable Battery Saver mode.',
      confidence: 'High Confidence (Hardware Sensor)',
      status: 'active',
      timestamp: now,
      evidence: {
        battery_percent: reading.battery_percent,
        plugged: reading.battery_plugged,
        secs_left: reading.battery_secs_left,
      },
    });
  }

  // Combined stress
  if (reading.cpu_percent >= thresholds.cpu_warning && reading.ram_percent >= thresholds.ram_warning) {
    insights.push({
      id: 'system_combined_stress',
      resource: 'System',
      severity: 'critical',
      title: 'Compounded System Workload Pressure',
      observed_value: `CPU: ${reading.cpu_percent.toFixed(1)}%, RAM: ${reading.ram_percent.toFixed(1)}%`,
      explanation: `Both CPU (${reading.cpu_percent.toFixed(1)}%) and RAM (${reading.ram_percent.toFixed(1)}%) are under simultaneous pressure. This causes desktop stutter, thrashing, and high response latency.`,
      possible_cause: 'Heavy multi-tasking, concurrent compilation, or runaway background services.',
      recommendation: 'Pause background tasks. Close high-memory browser tabs. Allow current jobs to finish.',
      confidence: 'Moderate Confidence (Joint Correlated Metrics)',
      status: 'active',
      timestamp: now,
      evidence: {
        cpu: reading.cpu_percent,
        ram: reading.ram_percent,
      },
    });
  }

  return insights;
}

/**
 * Recommendation Engine (JS port)
 */
export function generateRecommendations(insights) {
  const recs = [];

  for (const ins of insights) {
    if (ins.status !== 'active' && ins.status !== 'new' && ins.status !== 'ongoing') continue;

    if (ins.resource === 'CPU') {
      const procs = (ins.evidence?.top_processes || []).map(p => p.name).slice(0, 2).join(', ') || 'heavy processes';
      recs.push({
        id: `rec_${ins.id}`,
        title: `Investigate CPU-Intensive Tasks (${procs})`,
        priority: ins.severity === 'critical' ? 'High' : 'Medium',
        resource: 'CPU',
        insight_id: ins.id,
        reason: `Sustained processor workload (${ins.observed_value}) reduces scheduling availability.`,
        steps: [
          `Open Process Explorer and observe CPU usage of ${procs}.`,
          'Determine if these are intended workloads (rendering, compilation, etc).',
          'Close unneeded background services after saving your work.',
        ],
        benefit: 'Restores CPU scheduling cycles, reducing interface lag and thermal load.',
        safety: 'Do NOT terminate critical OS processes (System, csrss, svchost, explorer).',
      });
    } else if (ins.resource === 'RAM') {
      const procs = (ins.evidence?.top_processes || []).map(p => p.name).slice(0, 2).join(', ') || 'high-memory apps';
      recs.push({
        id: `rec_${ins.id}`,
        title: `Relieve Memory Pressure (${procs})`,
        priority: ins.severity === 'critical' ? 'High' : 'Medium',
        resource: 'RAM',
        insight_id: ins.id,
        reason: `Physical RAM allocation is high (${ins.observed_value}), increasing swap/paging risk.`,
        steps: [
          'Close inactive browser tabs and memory-heavy extensions.',
          'Close dormant IDEs, containers, or VMs not currently needed.',
          'Avoid launching additional memory-intensive software.',
        ],
        benefit: 'Prevents disk swap paging thrash, keeping applications responsive.',
        safety: 'Save unsaved documents before closing applications.',
      });
    } else if (ins.resource === 'Disk') {
      recs.push({
        id: `rec_${ins.id}`,
        title: `Reclaim Free Storage Capacity`,
        priority: ins.severity === 'critical' ? 'High' : 'Medium',
        resource: 'Disk',
        insight_id: ins.id,
        reason: `Storage volume has limited space remaining (${ins.observed_value}).`,
        steps: [
          'Run Disk Cleanup or Storage Sense to clear temporary files.',
          'Inspect Downloads and Videos for forgotten large files.',
          'Empty the Recycle Bin after verifying deleted items.',
        ],
        benefit: 'Ensures sufficient margin for OS updates, paging files, and logs.',
        safety: 'Review files manually before deleting. Never delete system files.',
      });
    } else if (ins.resource === 'Battery') {
      recs.push({
        id: `rec_${ins.id}`,
        title: ins.severity === 'critical' ? 'Connect AC Power Immediately' : 'Connect Charger / Enable Battery Saver',
        priority: ins.severity === 'critical' ? 'High' : 'Medium',
        resource: 'Battery',
        insight_id: ins.id,
        reason: `Battery level low (${ins.observed_value}) on DC power.`,
        steps: [
          'Plug laptop into AC mains power adapter.',
          'If away from power, save all open work immediately.',
          'Enable Battery Saver and reduce display brightness.',
        ],
        benefit: 'Protects against sudden shutdown and data loss.',
        safety: 'Ensure correct charger wattage to avoid battery wear.',
      });
    } else if (ins.resource === 'System') {
      recs.push({
        id: `rec_${ins.id}`,
        title: 'Address Concurrent CPU and Memory Contention',
        priority: 'High',
        resource: 'System',
        insight_id: ins.id,
        reason: 'Both processor and memory are concurrently saturated.',
        steps: [
          'Pause background sync, backups, or batch jobs.',
          'Use Process Explorer to isolate competing applications.',
          'Allow current heavy tasks to complete before starting new ones.',
        ],
        benefit: 'Alleviates bottlenecking across memory bus and CPU pipelines.',
        safety: 'Avoid force-restarting during active disk/compile operations.',
      });
    }
  }

  const priority = { High: 1, Medium: 2, Low: 3 };
  recs.sort((a, b) => (priority[a.priority] || 4) - (priority[b.priority] || 4));
  return recs;
}
