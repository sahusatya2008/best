import React from 'react';
import {
  Activity,
  BarChart3,
  BookOpen,
  Cpu,
  FlaskConical,
  Globe,
  GitCompare,
  Network,
  Radar,
  UserCheck,
} from 'lucide-react';
import type { TabId } from '../types/eidolon';
import { useEidolonStore } from '../store/useEidolonStore';

const NAV_ITEMS: Array<{ id: TabId; label: string; section: string; icon: React.ComponentType<any> }> = [
  { id: 'command', label: 'Command Centre', section: 'A', icon: Activity },
  { id: 'explorer', label: 'Society Explorer', section: 'B', icon: Globe },
  { id: 'agent', label: 'Agent Observatory', section: 'C', icon: UserCheck },
  { id: 'network', label: 'Social Network', section: 'D', icon: Network },
  { id: 'lab', label: 'Research Lab', section: 'E', icon: FlaskConical },
  { id: 'emergence', label: 'Emergence', section: 'F', icon: Radar },
  { id: 'analytics', label: 'Data & Analytics', section: 'G', icon: BarChart3 },
  { id: 'scenarios', label: 'Scenarios & Snapshots', section: 'H', icon: BookOpen },
  { id: 'compare', label: 'Compare Trials', section: 'I', icon: GitCompare },
  { id: 'diagnostics', label: 'Diagnostics', section: 'J', icon: Cpu },
];

export const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab, wsConnected } = useEidolonStore();

  return (
    <aside className="w-60 shrink-0 bg-[#0d1014] border-r border-[#232a35] flex flex-col justify-between">
      <div>
        <div className="px-4 py-4 border-b border-[#232a35]">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-sky-400 shadow-[0_0_8px_#38bdf8]" />
            <span className="font-mono text-sm font-bold tracking-[0.2em] text-slate-100">
              EIDOLON
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400 leading-tight">
            Computational Sociology &amp; Autonomous Society Lab
          </p>
        </div>

        <nav className="p-2 space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded text-xs font-medium transition-colors ${
                  active
                    ? 'bg-sky-500/15 text-sky-300 border border-sky-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="truncate">{item.label}</span>
                <span className="ml-auto font-mono text-[10px] opacity-50">{item.section}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-3 border-t border-[#232a35] text-[11px] text-slate-400 space-y-1.5">
        <div className="flex items-center justify-between">
          <span>Local Engine</span>
          <span className="font-mono text-emerald-400">100% OFFLINE</span>
        </div>
        <div className="flex items-center justify-between">
          <span>External AI</span>
          <span className="font-mono text-slate-300">NONE</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Live Stream</span>
          <span className={`font-mono ${wsConnected ? 'text-sky-400' : 'text-amber-400'}`}>
            {wsConnected ? 'WS ACTIVE' : 'POLLING'}
          </span>
        </div>
      </div>
    </aside>
  );
};
