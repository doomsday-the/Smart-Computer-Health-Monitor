import { BrowserRouter, Routes, Route, useLocation, useNavigate, Outlet } from 'react-router-dom';
import './index.css';
import Sidebar from './components/Sidebar';
import ErrorBoundary from './components/ErrorBoundary';
import { TelemetryProvider } from './context/TelemetryContext';

import OverviewPage        from './pages/OverviewPage';
import ResourceMonitorPage from './pages/ResourceMonitorPage';
import ProcessExplorerPage from './pages/ProcessExplorerPage';
import InsightsPage        from './pages/InsightsPage';
import RecommendationsPage from './pages/RecommendationsPage';
import HistoryPage         from './pages/HistoryPage';
import SettingsPage        from './pages/SettingsPage';
import AboutPage           from './pages/AboutPage';

function LayoutWrapper() {
  const location  = useLocation();
  const navigate  = useNavigate();
  const segment   = location.pathname.split('/').filter(Boolean)[0] || 'overview';

  return (
    <div className="app-layout">
      <Sidebar activePage={segment} onNavigate={(page) => navigate(`/${page}`)} />
      <div className="main-content">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <TelemetryProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LayoutWrapper />}>
            <Route index                  element={<OverviewPage />}        />
            <Route path="overview"        element={<OverviewPage />}        />
            <Route path="resources"       element={<ResourceMonitorPage />} />
            <Route path="processes"       element={<ProcessExplorerPage />} />
            <Route path="insights"        element={<InsightsPage />}        />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="history"         element={<HistoryPage />}         />
            <Route path="settings"        element={<SettingsPage />}        />
            <Route path="about"           element={<AboutPage />}           />
          </Route>
        </Routes>
      </BrowserRouter>
    </TelemetryProvider>
  );
}
