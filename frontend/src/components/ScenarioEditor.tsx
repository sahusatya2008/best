import React, { useState } from 'react';
import { Archive, PlayCircle, RotateCcw } from 'lucide-react';
import { api } from '../api/client';
import { useEidolonStore } from '../store/useEidolonStore';

export const ScenarioEditor: React.FC = () => {
  const { scenarios, snapshots, fetchAll, setActiveTab } = useEidolonStore();
  const [snapLabel, setSnapLabel] = useState('checkpoint');
  const [backupMsg, setBackupMsg] = useState<string | null>(null);

  const handleLoadScenario = async (scenarioId: string) => {
    await api.createExperiment({ scenario_id: scenarioId });
    await fetchAll();
    setActiveTab('command');
  };

  const handleCreateSnapshot = async () => {
    await api.createSnapshot(snapLabel || 'checkpoint');
    await fetchAll();
  };

  const handleRestore = async (snapId: string) => {
    await api.restoreSnapshot(snapId);
    await fetchAll();
  };

  const handleBackup = async () => {
    const res = await api.createBackup();
    setBackupMsg(`SQLite backup saved: ${res.filename}`);
  };

  return (
    <div className="space-y-4">
      <div className="panel">
        <div className="panel-header">Eight Prebuilt Scientific Scenarios</div>
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          {scenarios.map((sc) => (
            <div key={sc.scenario_id} className="bg-[#0b0d10] border border-[#232a35] rounded p-3.5 flex flex-col justify-between gap-2.5">
              <div>
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-semibold text-sky-300">{sc.title}</h3>
                  <span className="font-mono text-[10px] text-slate-400">
                    N={sc.config.population_size} • seed={sc.config.seed}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-300">{sc.research_question}</p>
                <div className="mt-2 flex flex-wrap gap-2 font-mono text-[10px] text-slate-400">
                  <span>scarcity={sc.config.scarcity}</span>
                  <span>coop_reward={sc.config.cooperation_reward}</span>
                  <span>climate={sc.config.climate_severity}</span>
                  <span>cultural_rate={sc.config.cultural_transmission_rate}</span>
                </div>
              </div>
              <button
                onClick={() => handleLoadScenario(sc.scenario_id)}
                className="flex items-center justify-center gap-1.5 py-1.5 rounded bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 border border-sky-500/30 text-xs font-medium"
              >
                <PlayCircle className="w-3.5 h-3.5" /> Initialize Scenario
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="panel-header flex flex-wrap justify-between items-center gap-2">
          <span>Versioned Simulation Snapshots &amp; Local SQLite Backups</span>
          <div className="flex items-center gap-2 normal-case">
            <input
              value={snapLabel}
              onChange={(e) => setSnapLabel(e.target.value)}
              placeholder="Snapshot label"
              className="bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1 text-xs text-slate-200"
            />
            <button
              onClick={handleCreateSnapshot}
              className="px-2.5 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white text-xs"
            >
              Save Snapshot
            </button>
            <button
              onClick={handleBackup}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs border border-[#2d3644]"
            >
              <Archive className="w-3.5 h-3.5" /> Backup DB
            </button>
          </div>
        </div>
        {backupMsg && <div className="px-4 py-2 text-xs font-mono text-emerald-300">{backupMsg}</div>}
        <div className="divide-y divide-[#1a2029] text-xs font-mono max-h-64 overflow-y-auto">
          {snapshots.map((s) => (
            <div key={s.snapshot_id} className="px-4 py-2 flex items-center justify-between gap-2">
              <div>
                <span className="text-sky-300">{s.label}</span>
                <span className="text-slate-400 ml-3">exp={s.experiment_id} • tick={s.tick}</span>
                <span className="text-slate-500 ml-3">{(s.size_bytes / 1024).toFixed(1)} KB</span>
              </div>
              <button
                onClick={() => handleRestore(s.snapshot_id)}
                className="flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30"
              >
                <RotateCcw className="w-3 h-3" /> Restore
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
