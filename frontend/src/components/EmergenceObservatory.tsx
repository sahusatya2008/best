import React, { useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { useEidolonStore } from '../store/useEidolonStore';

export const EmergenceObservatory: React.FC = () => {
  const { emergentPatterns, refreshMetricsAndEmergence, summary } = useEidolonStore();

  useEffect(() => {
    refreshMetricsAndEmergence();
  }, [summary?.clock.tick]);

  return (
    <div className="space-y-4">
      <div className="panel p-3.5 flex justify-between items-center">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">Emergent Behaviour Detection Engine</h2>
          <p className="text-xs text-slate-400">
            Strictly empirical pattern detection comparing baseline windows, network modularity, Gini inequality, and cultural entropy.
          </p>
        </div>
        <button
          onClick={() => refreshMetricsAndEmergence()}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-[#2d3644]"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-evaluate
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {emergentPatterns.map((p) => (
          <div key={p.pattern_id} className="panel p-4 space-y-2.5">
            <div className="flex justify-between items-start gap-2">
              <div>
                <span className="font-mono text-[10px] uppercase px-2 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20">
                  {p.category.replace(/_/g, ' ')}
                </span>
                <h3 className="mt-1.5 text-sm font-semibold text-slate-100">{p.title}</h3>
              </div>
              <div className="text-right font-mono text-xs">
                <div className={p.delta >= 0 ? 'text-emerald-300' : 'text-rose-300'}>
                  Δ {p.delta >= 0 ? '+' : ''}
                  {p.delta.toFixed(4)}
                </div>
                <div className="text-[10px] text-slate-400">conf {(p.confidence_score * 100).toFixed(0)}%</div>
              </div>
            </div>

            <p className="text-xs text-slate-200 leading-relaxed">{p.measured_claim}</p>

            <div className="text-[11px] text-slate-400 border-t border-[#232a35] pt-2">
              <span className="text-slate-500">Method: </span>
              {p.measurement_method}
            </div>

            <div className="bg-[#0b0d10] border border-[#1f2630] rounded p-2 font-mono text-[10px] text-slate-300 overflow-x-auto">
              {JSON.stringify(p.supporting_data)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
