import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { OsSimulator } from '../engine/simulator';
import { calculateHealthScore, generateInsights, generateRecommendations } from '../engine/analysis';

const TelemetryContext = createContext(null);

const POLL_INTERVAL = 1500; // ms

export function TelemetryProvider({ children }) {
  const simulatorRef = useRef(null);
  const [reading, setReading] = useState(null);
  const [health, setHealth] = useState(null);
  const [insights, setInsights] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [history, setHistory] = useState({ cpu: [], ram: [], disk: [], timestamps: [] });
  const [isLive, setIsLive] = useState(true);
  const [scenario, setScenario] = useState('auto');
  const [alertCount, setAlertCount] = useState(0);

  // Deep history for the History page (keeps more data points)
  const [deepHistory, setDeepHistory] = useState([]);

  useEffect(() => {
    simulatorRef.current = new OsSimulator();
  }, []);

  const poll = useCallback(() => {
    if (!simulatorRef.current || !isLive) return;

    const data = simulatorRef.current.tick();
    setReading(data);

    const h = calculateHealthScore(data);
    setHealth(h);

    const ins = generateInsights(data);
    setInsights(ins);
    setAlertCount(ins.filter(i => i.severity === 'critical' || i.severity === 'warning').length);

    const recs = generateRecommendations(ins);
    setRecommendations(recs);

    setHistory({
      cpu: [...simulatorRef.current.history.cpu],
      ram: [...simulatorRef.current.history.ram],
      disk: [...simulatorRef.current.history.disk],
      timestamps: [...simulatorRef.current.history.timestamps],
    });

    // Save snapshot for deep history
    setDeepHistory(prev => {
      const entry = {
        timestamp: data.timestamp,
        cpu: data.cpu_percent,
        ram: data.ram_percent,
        disk: data.disk_percent,
        battery: data.battery_percent,
        score: h.score,
        classification: h.classification,
      };
      const updated = [...prev, entry];
      // Keep last 500 entries (~12.5 min at 1.5s interval)
      return updated.length > 500 ? updated.slice(-500) : updated;
    });
  }, [isLive]);

  useEffect(() => {
    // Initial tick
    poll();
    const interval = setInterval(poll, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [poll]);

  const changeScenario = useCallback((name) => {
    if (!simulatorRef.current) return;
    if (name === 'auto') {
      simulatorRef.current.enableAutoScenario();
    } else {
      simulatorRef.current.setScenario(name);
    }
    setScenario(name);
  }, []);

  const toggleLive = useCallback(() => {
    setIsLive(prev => !prev);
  }, []);

  const value = {
    reading,
    health,
    insights,
    recommendations,
    history,
    deepHistory,
    isLive,
    scenario,
    alertCount,
    changeScenario,
    toggleLive,
  };

  return (
    <TelemetryContext.Provider value={value}>
      {children}
    </TelemetryContext.Provider>
  );
}

export function useTelemetry() {
  const ctx = useContext(TelemetryContext);
  if (!ctx) throw new Error('useTelemetry must be used within TelemetryProvider');
  return ctx;
}
