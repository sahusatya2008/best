import React, { useState } from 'react';
import { Download } from 'lucide-react';
import { api } from '../api/client';
import { useEidolonStore } from '../store/useEidolonStore';
import { PlotlyChart } from './PlotlyChart';

export const DataAnalytics: React.FC = () => {
  const { metricsHistory } = useEidolonStore();
  const [exportInfo, setExportInfo] = useState<any | null>(null);

  const ticks = metricsHistory.map((r) => r.tick);

  const handleExport = async () => {
    const res = await api.exportExperiment();
    setExportInfo(res);
  };

  return (
    <div className="space-y-4">
      <div className="panel p-3.5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">Scientific Time-Series &amp; Report Export</h2>
          <p className="text-xs text-slate-400">
            All plots reflect computed backend simulation state across {metricsHistory.length} recorded ticks.
          </p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium"
        >
          <Download className="w-3.5 h-3.5" /> Generate JSON + CSV + Matplotlib Report
        </button>
      </div>

      {exportInfo && (
        <div className="panel p-3.5 space-y-2 text-xs">
          <div className="font-semibold text-emerald-300">Report Bundle Exported Locally</div>
          <div className="flex flex-wrap gap-3 font-mono text-[11px]">
            <a href={exportInfo.json_url} target="_blank" rel="noreferrer" className="text-sky-300 underline">
              Download JSON Bundle
            </a>
            <a href={exportInfo.csv_url} target="_blank" rel="noreferrer" className="text-sky-300 underline">
              Download Metrics CSV
            </a>
            <a href={exportInfo.chart_url} target="_blank" rel="noreferrer" className="text-sky-300 underline">
              Download Matplotlib PNG
            </a>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel p-2">
          <div className="panel-header">Cooperation, Trust &amp; Collective Success</div>
          <PlotlyChart
            data={[
              { x: ticks, y: metricsHistory.map((r) => r.cooperation_index), name: 'Cooperation Index', line: { color: '#34d399' } },
              { x: ticks, y: metricsHistory.map((r) => r.mean_trust), name: 'Mean Trust', line: { color: '#38bdf8' } },
              { x: ticks, y: metricsHistory.map((r) => r.collective_success_rate), name: 'Collective Success', line: { color: '#fbbf24' } },
            ]}
          />
        </div>

        <div className="panel p-2">
          <div className="panel-header">Inequality (Gini) &amp; Cultural Diversity</div>
          <PlotlyChart
            data={[
              { x: ticks, y: metricsHistory.map((r) => r.gini_coefficient), name: 'Gini Coefficient', line: { color: '#fb7185' } },
              { x: ticks, y: metricsHistory.map((r) => r.cultural_diversity), name: 'Cultural Diversity', line: { color: '#a78bfa' } },
            ]}
          />
        </div>

        <div className="panel p-2">
          <div className="panel-header">Reinforcement Learning &amp; Utility</div>
          <PlotlyChart
            data={[
              { x: ticks, y: metricsHistory.map((r) => r.mean_q_value), name: 'Mean Q-Value', line: { color: '#38bdf8' } },
              { x: ticks, y: metricsHistory.map((r) => r.mean_utility), name: 'Mean Action Utility', line: { color: '#34d399' } },
              { x: ticks, y: metricsHistory.map((r) => r.avg_need_satisfaction), name: 'Need Satisfaction', line: { color: '#fbbf24' } },
            ]}
          />
        </div>

        <div className="panel p-2">
          <div className="panel-header">Trade Volume, Communities &amp; Institutions</div>
          <PlotlyChart
            data={[
              { x: ticks, y: metricsHistory.map((r) => r.trade_volume), name: 'Trade Volume', line: { color: '#38bdf8' } },
              { x: ticks, y: metricsHistory.map((r) => r.community_count), name: 'Communities', line: { color: '#a78bfa' } },
              { x: ticks, y: metricsHistory.map((r) => r.institution_count), name: 'Institutions', line: { color: '#34d399' } },
            ]}
          />
        </div>
      </div>
    </div>
  );
};
