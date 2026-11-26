import React, { useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { CommandCentre } from './components/CommandCentre';
import { SocietyExplorer } from './components/SocietyExplorer';
import { AgentObservatory } from './components/AgentObservatory';
import { SocialNetworkObservatory } from './components/SocialNetworkObservatory';
import { ResearchLaboratory } from './components/ResearchLaboratory';
import { EmergenceObservatory } from './components/EmergenceObservatory';
import { DataAnalytics } from './components/DataAnalytics';
import { ScenarioEditor } from './components/ScenarioEditor';
import { ExperimentComparison } from './components/ExperimentComparison';
import { SystemDiagnostics } from './components/SystemDiagnostics';
import { useEidolonStore } from './store/useEidolonStore';

export function App() {
  const { activeTab, fetchAll, connectWebSocket, error } = useEidolonStore();

  useEffect(() => {
    fetchAll();
    const closeWs = connectWebSocket();
    return () => closeWs();
  }, [fetchAll, connectWebSocket]);

  const renderTab = () => {
    switch (activeTab) {
      case 'command':
        return <CommandCentre />;
      case 'explorer':
        return <SocietyExplorer />;
      case 'agent':
        return <AgentObservatory />;
      case 'network':
        return <SocialNetworkObservatory />;
      case 'lab':
        return <ResearchLaboratory />;
      case 'emergence':
        return <EmergenceObservatory />;
      case 'analytics':
        return <DataAnalytics />;
      case 'scenarios':
        return <ScenarioEditor />;
      case 'compare':
        return <ExperimentComparison />;
      case 'diagnostics':
        return <SystemDiagnostics />;
      default:
        return <CommandCentre />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0d10] text-slate-200 flex">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        {error && (
          <div className="mx-5 mt-3 px-3 py-2 rounded bg-rose-950/60 border border-rose-700/50 text-xs font-mono text-rose-200">
            {error}
          </div>
        )}
        <main className="flex-1 p-5 overflow-y-auto sci-grid-bg">{renderTab()}</main>
      </div>
    </div>
  );
}

export default App;
