import React from 'react';
import { FastForward, Pause, Play, Save, Square, StepForward } from 'lucide-react';
import { api } from '../api/client';
import { useEidolonStore } from '../store/useEidolonStore';

export const TopBar: React.FC = () => {
  const {
    status,
    summary,
    tickIntervalMs,
    runSimulation,
    pauseSimulation,
    stopSimulation,
    stepSimulation,
    fetchAll,
  } = useEidolonStore();

  const handleSpeed = async (ms: number) => {
    await api.patchConfig({ tick_interval_ms: ms });
    useEidolonStore.setState({ tickIntervalMs: ms });
  };

  const handleSaveSnapshot = async () => {
    await api.createSnapshot(`manual_t${summary?.clock.tick ?? 0}`);
    await fetchAll();
  };

  const isRunning = status === 'running';

  return (
    <header className="h-14 shrink-0 bg-[#111419] border-b border-[#232a35] px-5 flex items-center justify-between gap-4">
      <div className="flex items-center gap-4 min-w-0">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold text-slate-100 truncate">
              {summary?.config.name || 'Loading experiment...'}
            </h1>
            <span
              className={`px-2 py-0.5 rounded font-mono text-[10px] uppercase border ${
                isRunning
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                  : status === 'completed'
                  ? 'bg-sky-500/15 text-sky-300 border-sky-500/30'
                  : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
              }`}
            >
              {status}
            </span>
          </div>
          <div className="text-[11px] font-mono text-slate-400 flex items-center gap-3">
            <span>TICK {summary?.clock.tick ?? 0}</span>
            <span>DAY {summary?.clock.day ?? 0}</span>
            <span className="uppercase">{summary?.clock.season ?? 'spring'}</span>
            <span>YEAR {summary?.clock.year ?? 1}</span>
            <span>SEED {summary?.config.seed ?? 42}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {!isRunning ? (
          <button
            onClick={() => runSimulation(tickIntervalMs)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium"
          >
            <Play className="w-3.5 h-3.5" /> Run
          </button>
        ) : (
          <button
            onClick={() => pauseSimulation()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium"
          >
            <Pause className="w-3.5 h-3.5" /> Pause
          </button>
        )}

        <button
          onClick={() => stepSimulation(1)}
          disabled={isRunning}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 text-xs font-mono border border-[#2d3644]"
        >
          <StepForward className="w-3.5 h-3.5" /> +1
        </button>

        <button
          onClick={() => stepSimulation(25)}
          disabled={isRunning}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 text-xs font-mono border border-[#2d3644]"
        >
          <FastForward className="w-3.5 h-3.5" /> +25
        </button>

        <button
          onClick={() => stopSimulation()}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded bg-rose-900/50 hover:bg-rose-800/70 text-rose-200 text-xs border border-rose-700/40"
        >
          <Square className="w-3 h-3" /> Stop
        </button>

        <div className="h-5 w-px bg-[#232a35] mx-1" />

        <label className="flex items-center gap-1.5 text-[11px] text-slate-400">
          <span>Interval</span>
          <select
            value={tickIntervalMs}
            onChange={(e) => handleSpeed(Number(e.target.value))}
            className="bg-[#0b0d10] border border-[#232a35] rounded px-1.5 py-1 font-mono text-xs text-slate-200"
          >
            <option value={25}>25ms</option>
            <option value={60}>60ms</option>
            <option value={120}>120ms</option>
            <option value={250}>250ms</option>
            <option value={500}>500ms</option>
          </select>
        </label>

        <button
          onClick={handleSaveSnapshot}
          title="Save Versioned Snapshot"
          className="flex items-center gap-1 px-2.5 py-1.5 rounded bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 text-xs border border-sky-500/30"
        >
          <Save className="w-3.5 h-3.5" /> Snapshot
        </button>
      </div>
    </header>
  );
};
