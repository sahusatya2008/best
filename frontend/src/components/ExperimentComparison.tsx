import React, { useState } from 'react';
import { api } from '../api/client';
import { useEidolonStore } from '../store/useEidolonStore';

export const ExperimentComparison: React.FC = () => {
  const { experiments, scenarios } = useEidolonStore();
  const [expA, setExpA] = useState(experiments[0]?.id || '');
  const [expB, setExpB] = useState(experiments[1]?.id || experiments[0]?.id || '');
  const [scenA, setScenA] = useState('scarcity_experiment');
  const [scenB, setScenB] = useState('cooperation_experiment');
  const [seedsStr, setSeedsStr] = useState('42, 101, 202');
  const [ticks, setTicks] = useState(50);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  const runSavedCompare = async () => {
    if (!expA || !expB) return;
    setLoading(true);
    try {
      const res = await api.compareExperiments({
        mode: 'saved',
        experiment_a_id: expA,
        experiment_b_id: expB,
      });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const runControlledTrials = async () => {
    setLoading(true);
    try {
      const ca = scenarios.find((s) => s.scenario_id === scenA)?.config;
      const cb = scenarios.find((s) => s.scenario_id === scenB)?.config;
      const seeds = seedsStr
        .split(',')
        .map((x) => parseInt(x.trim(), 10))
        .filter((n) => !Number.isNaN(n));
      const res = await api.compareExperiments({
        mode: 'controlled_trials',
        config_a: { ...ca, population_size: Math.min(60, ca?.population_size || 60) },
        config_b: { ...cb, population_size: Math.min(60, cb?.population_size || 60) },
        seeds: seeds.length ? seeds : [42, 101, 202],
        ticks,
      });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="panel p-4 space-y-3 text-xs">
          <div className="font-semibold uppercase tracking-wider text-slate-300">
            Compare Saved Experiments
          </div>
          <div className="grid grid-cols-2 gap-2">
            <select
              value={expA}
              onChange={(e) => setExpA(e.target.value)}
              className="bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1.5 text-slate-200"
            >
              {experiments.map((e) => (
                <option key={e.id} value={e.id}>
                  A: {e.name} (t={e.current_tick})
                </option>
              ))}
            </select>
            <select
              value={expB}
              onChange={(e) => setExpB(e.target.value)}
              className="bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1.5 text-slate-200"
            >
              {experiments.map((e) => (
                <option key={e.id} value={e.id}>
                  B: {e.name} (t={e.current_tick})
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={runSavedCompare}
            disabled={loading}
            className="px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white"
          >
            Compare Saved Histories
          </button>
        </div>

        <div className="panel p-4 space-y-3 text-xs">
          <div className="font-semibold uppercase tracking-wider text-slate-300">
            Controlled Multi-Seed Trials (Mean, Variance &amp; 95% CI)
          </div>
          <div className="grid grid-cols-2 gap-2">
            <select
              value={scenA}
              onChange={(e) => setScenA(e.target.value)}
              className="bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1.5 text-slate-200"
            >
              {scenarios.map((s) => (
                <option key={s.scenario_id} value={s.scenario_id}>
                  A: {s.title}
                </option>
              ))}
            </select>
            <select
              value={scenB}
              onChange={(e) => setScenB(e.target.value)}
              className="bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1.5 text-slate-200"
            >
              {scenarios.map((s) => (
                <option key={s.scenario_id} value={s.scenario_id}>
                  B: {s.title}
                </option>
              ))}
            </select>
            <input
              value={seedsStr}
              onChange={(e) => setSeedsStr(e.target.value)}
              placeholder="Seeds e.g. 42, 101, 202"
              className="bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1.5 font-mono text-slate-200"
            />
            <input
              type="number"
              value={ticks}
              min={10}
              max={300}
              onChange={(e) => setTicks(Number(e.target.value))}
              className="bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1.5 font-mono text-slate-200"
            />
          </div>
          <button
            onClick={runControlledTrials}
            disabled={loading}
            className="px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white"
          >
            {loading ? 'Running Paired Trials...' : 'Run Multi-Seed Controlled Comparison'}
          </button>
        </div>
      </div>

      {result && result.metrics && (
        <div className="panel overflow-x-auto">
          <div className="panel-header">Statistical Comparison Results</div>
          <table className="w-full text-xs font-mono">
            <thead className="bg-[#0d1014] text-slate-400 border-b border-[#232a35]">
              <tr>
                <th className="text-left px-3 py-2">Metric</th>
                <th className="text-right px-3 py-2">Exp A Mean (95% CI)</th>
                <th className="text-right px-3 py-2">Exp B Mean (95% CI)</th>
                <th className="text-right px-3 py-2">Diff (B - A)</th>
                <th className="text-right px-3 py-2">p-value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1a2029]">
              {Object.entries(result.metrics).map(([metric, row]: [string, any]) => (
                <tr key={metric} className="hover:bg-slate-800/30">
                  <td className="px-3 py-2 text-slate-200">{metric}</td>
                  <td className="px-3 py-2 text-right text-sky-300">
                    {row.experiment_a.mean.toFixed(4)} [{row.experiment_a.ci95_low.toFixed(3)}, {row.experiment_a.ci95_high.toFixed(3)}]
                  </td>
                  <td className="px-3 py-2 text-right text-emerald-300">
                    {row.experiment_b.mean.toFixed(4)} [{row.experiment_b.ci95_low.toFixed(3)}, {row.experiment_b.ci95_high.toFixed(3)}]
                  </td>
                  <td className={`px-3 py-2 text-right ${row.mean_diff_b_minus_a >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                    {row.mean_diff_b_minus_a >= 0 ? '+' : ''}
                    {row.mean_diff_b_minus_a.toFixed(4)}
                  </td>
                  <td className="px-3 py-2 text-right text-slate-400">
                    {row.p_value !== undefined ? row.p_value.toFixed(4) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
