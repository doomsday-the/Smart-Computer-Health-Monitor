/**
 * OS Telemetry Simulator
 * 
 * Produces realistic, time-varying system readings that mirror
 * the Python SystemReading dataclass. Uses layered sine waves and
 * Perlin-like noise to create natural-looking fluctuations rather
 * than flat random values.
 */

// Deterministic seeded noise for smooth curves
function smoothNoise(t, frequency = 1, phase = 0) {
  return Math.sin(t * frequency + phase) * 0.5 + 0.5;
}

function layeredNoise(t, seed = 0) {
  const v =
    0.5 * smoothNoise(t, 0.3, seed) +
    0.25 * smoothNoise(t, 0.7, seed + 1.3) +
    0.15 * smoothNoise(t, 1.5, seed + 2.7) +
    0.1 * smoothNoise(t, 3.1, seed + 4.1);
  return Math.max(0, Math.min(1, v));
}

// Maps a 0-1 noise value into a biased range
function mapRange(noise, min, max, bias = 0.5) {
  const biased = Math.pow(noise, 1 / bias);
  return min + biased * (max - min);
}

const SCENARIOS = {
  idle: {
    cpu: [8, 25],
    ram: [35, 50],
    disk: [40, 55],
    diskRead: [0, 5e6],
    diskWrite: [0, 2e6],
    battery: [70, 95],
    label: 'Idle',
  },
  normal: {
    cpu: [15, 45],
    ram: [45, 65],
    disk: [45, 60],
    diskRead: [1e6, 30e6],
    diskWrite: [0.5e6, 15e6],
    battery: [50, 85],
    label: 'Normal Workload',
  },
  heavy: {
    cpu: [60, 92],
    ram: [70, 90],
    disk: [55, 75],
    diskRead: [20e6, 100e6],
    diskWrite: [10e6, 60e6],
    battery: [25, 55],
    label: 'Heavy Workload',
  },
  stress: {
    cpu: [85, 99],
    ram: [88, 97],
    disk: [80, 95],
    diskRead: [50e6, 200e6],
    diskWrite: [30e6, 120e6],
    battery: [5, 20],
    label: 'Critical Stress',
  },
};

const FAKE_PROCESSES = [
  { name: 'chrome.exe', pid: 4820, baseCpu: 12, baseMem: 680 },
  { name: 'code.exe', pid: 7312, baseCpu: 8, baseMem: 520 },
  { name: 'node.exe', pid: 9104, baseCpu: 6, baseMem: 310 },
  { name: 'python.exe', pid: 2456, baseCpu: 15, baseMem: 240 },
  { name: 'explorer.exe', pid: 1120, baseCpu: 1, baseMem: 85 },
  { name: 'svchost.exe', pid: 980, baseCpu: 2, baseMem: 65 },
  { name: 'System', pid: 4, baseCpu: 0.5, baseMem: 20 },
  { name: 'msedge.exe', pid: 5678, baseCpu: 5, baseMem: 420 },
  { name: 'spotify.exe', pid: 3344, baseCpu: 3, baseMem: 190 },
  { name: 'discord.exe', pid: 6612, baseCpu: 4, baseMem: 280 },
  { name: 'taskmgr.exe', pid: 8890, baseCpu: 1, baseMem: 35 },
  { name: 'dwm.exe', pid: 768, baseCpu: 2, baseMem: 110 },
];

export class OsSimulator {
  constructor() {
    this._tick = 0;
    this._scenario = 'normal';
    this._transitionTarget = null;
    this._transitionProgress = 0;
    this._startTime = Date.now();
    this._autoScenario = true;

    // System constants
    this._totalRam = 16 * 1024 * 1024 * 1024; // 16 GB
    this._totalDisk = 512 * 1024 * 1024 * 1024; // 512 GB
    this._coreCount = 8;
    this._cpuFreq = 3200; // MHz

    // History for sparklines
    this.history = {
      cpu: [],
      ram: [],
      disk: [],
      timestamps: [],
    };
    this.maxHistory = 60;
  }

  setScenario(name) {
    if (SCENARIOS[name] && name !== this._scenario) {
      this._transitionTarget = name;
      this._transitionProgress = 0;
      this._autoScenario = false;
    }
  }

  enableAutoScenario() {
    this._autoScenario = true;
  }

  _getCurrentScenarioConfig() {
    if (this._autoScenario) {
      // Auto-cycle through scenarios with natural timing
      const elapsed = (Date.now() - this._startTime) / 1000;
      const cycle = elapsed % 180; // 3-minute cycle
      if (cycle < 40) this._scenario = 'idle';
      else if (cycle < 100) this._scenario = 'normal';
      else if (cycle < 150) this._scenario = 'heavy';
      else this._scenario = 'stress';
    }

    if (this._transitionTarget) {
      this._transitionProgress += 0.05;
      if (this._transitionProgress >= 1) {
        this._scenario = this._transitionTarget;
        this._transitionTarget = null;
        this._transitionProgress = 0;
      }
    }

    const base = SCENARIOS[this._scenario];
    if (this._transitionTarget && this._transitionProgress > 0) {
      const target = SCENARIOS[this._transitionTarget];
      const t = this._transitionProgress;
      return {
        cpu: [lerp(base.cpu[0], target.cpu[0], t), lerp(base.cpu[1], target.cpu[1], t)],
        ram: [lerp(base.ram[0], target.ram[0], t), lerp(base.ram[1], target.ram[1], t)],
        disk: [lerp(base.disk[0], target.disk[0], t), lerp(base.disk[1], target.disk[1], t)],
        diskRead: [lerp(base.diskRead[0], target.diskRead[0], t), lerp(base.diskRead[1], target.diskRead[1], t)],
        diskWrite: [lerp(base.diskWrite[0], target.diskWrite[0], t), lerp(base.diskWrite[1], target.diskWrite[1], t)],
        battery: [lerp(base.battery[0], target.battery[0], t), lerp(base.battery[1], target.battery[1], t)],
        label: target.label,
      };
    }
    return base;
  }

  tick() {
    this._tick++;
    const t = this._tick * 0.1;
    const sc = this._getCurrentScenarioConfig();

    const cpuPercent = clamp(mapRange(layeredNoise(t, 0), sc.cpu[0], sc.cpu[1]), 0, 100);
    const ramPercent = clamp(mapRange(layeredNoise(t, 10), sc.ram[0], sc.ram[1]), 0, 100);
    const diskPercent = clamp(mapRange(layeredNoise(t, 20), sc.disk[0], sc.disk[1]), 0, 100);

    const coresPercent = Array.from({ length: this._coreCount }, (_, i) => {
      const coreNoise = layeredNoise(t, 100 + i * 7);
      const base = cpuPercent * 0.6;
      return clamp(base + coreNoise * cpuPercent * 0.8, 0, 100);
    });

    const ramUsed = Math.round(this._totalRam * (ramPercent / 100));
    const ramAvail = this._totalRam - ramUsed;

    const diskUsed = Math.round(this._totalDisk * (diskPercent / 100));
    const diskFree = this._totalDisk - diskUsed;

    const diskRead = mapRange(layeredNoise(t, 30), sc.diskRead[0], sc.diskRead[1]);
    const diskWrite = mapRange(layeredNoise(t, 40), sc.diskWrite[0], sc.diskWrite[1]);

    const battPercent = clamp(mapRange(layeredNoise(t, 50), sc.battery[0], sc.battery[1]), 0, 100);
    const battPlugged = battPercent > 80;

    // Update history
    const now = new Date().toISOString();
    this.history.cpu.push(cpuPercent);
    this.history.ram.push(ramPercent);
    this.history.disk.push(diskPercent);
    this.history.timestamps.push(now);
    if (this.history.cpu.length > this.maxHistory) {
      this.history.cpu.shift();
      this.history.ram.shift();
      this.history.disk.shift();
      this.history.timestamps.shift();
    }

    // Generate process list with dynamic values
    const processes = FAKE_PROCESSES.map((p, i) => {
      const cpuMult = cpuPercent / 30;
      const noise = layeredNoise(t, 200 + i * 3);
      const procCpu = clamp(p.baseCpu * cpuMult * (0.3 + noise * 1.4), 0, 100);
      const procMem = Math.round(p.baseMem * (0.6 + noise * 0.8));
      return {
        name: p.name,
        pid: p.pid,
        cpu_percent: Math.round(procCpu * 10) / 10,
        memory_used_bytes: procMem * 1024 * 1024,
        memory_percent: Math.round((procMem / (this._totalRam / 1024 / 1024)) * 1000) / 10,
        status: 'running',
      };
    });

    return {
      timestamp: now,
      cpu_percent: Math.round(cpuPercent * 10) / 10,
      cpu_frequency_mhz: this._cpuFreq + Math.round(layeredNoise(t, 60) * 400 - 200),
      cpu_cores_percent: coresPercent.map(v => Math.round(v * 10) / 10),
      ram_percent: Math.round(ramPercent * 10) / 10,
      ram_used_bytes: ramUsed,
      ram_available_bytes: ramAvail,
      ram_total_bytes: this._totalRam,
      disk_path: 'C:\\',
      disk_used_bytes: diskUsed,
      disk_free_bytes: diskFree,
      disk_total_bytes: this._totalDisk,
      disk_percent: Math.round(diskPercent * 10) / 10,
      disk_read_bytes_sec: Math.round(diskRead),
      disk_write_bytes_sec: Math.round(diskWrite),
      battery_available: true,
      battery_percent: Math.round(battPercent * 10) / 10,
      battery_plugged: battPlugged,
      battery_secs_left: battPlugged ? null : Math.round(battPercent * 60),
      processes,
      scenario: sc.label || this._scenario,
    };
  }
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}
