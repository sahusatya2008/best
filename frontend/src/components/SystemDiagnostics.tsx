import React, { useEffect } from 'react';
import { useEidolonStore } from '../store/useEidolonStore';

export const SystemDiagnostics: React.FC = () => {
  const { diagnostics, refreshMetricsAndEmergence } = useEidolonStore();

  useEffect(() => {
    refreshMetricsAndEmergence();
  }, []);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="panel p-3.5">
          <div className="text-[11px] uppercase text-slate-400">Last / Avg Tick Latency</div>
          <div className="mt-1 font-mono text-lg text-sky-300">
            {diagnostics?.last_tick_ms ?? 0} ms / {diagnostics?.avg_tick_ms ?? 0} ms
          </div>
        </div>
        <div className="panel p-3.5">
          <div className="text-[11px] uppercase text-slate-400">Theoretical Max TPS</div>
          <div className="mt-1 font-mono text-lg text-emerald-300">
            {diagnostics?.theoretical_max_tps ?? 0} ticks/s
          </div>
        </div>
        <div className="panel p-3.5">
          <div className="text-[11px] uppercase text-slate-400">Process RSS Memory</div>
          <div className="mt-1 font-mono text-lg text-amber-300">{diagnostics?.memory_mb ?? 0} MB</div>
        </div>
        <div className="panel p-3.5">
          <div className="text-[11px] uppercase text-slate-400">SQLite Database</div>
          <div className="mt-1 font-mono text-lg text-violet-300">
            {diagnostics?.database?.size_mb ?? 0} MB
          </div>
          <div className="text-[10px] font-mono text-slate-400">
            {diagnostics?.database?.events ?? 0} events • {diagnostics?.database?.snapshots ?? 0} snapshots
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="panel p-4 text-xs">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Active Computational Subsystems
          </div>
          <div className="space-y-2 font-mono">
            {Object.entries(diagnostics?.active_subsystems || {}).map(([sub, active]) => (
              <div key={sub} className="flex justify-between py-1 border-b border-[#1b212b]">
                <span className="text-slate-300">{sub}</span>
                <span
                  className={
                    sub === 'external_ai_dependencies'
                      ? active
                        ? 'text-rose-400'
                        : 'text-emerald-400'
                      : active
                      ? 'text-emerald-400'
                      : 'text-slate-500'
                  }
                >
                  {String(active).toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel p-4 text-xs">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Runtime Error Log
          </div>
          {diagnostics?.error_logs?.length ? (
            <div className="space-y-1.5 font-mono text-rose-300">
              {diagnostics.error_logs.map((err: any, i: number) => (
                <div key={i}>{JSON.stringify(err)}</div>
              ))}
            </div>
          ) : (
            <div className="text-slate-400 font-mono">0 runtime errors logged.</div>
          )}
        </div>
      </div>
    </div>
  );
};
