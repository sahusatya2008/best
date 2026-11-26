import React from 'react';
import { useEidolonStore } from '../store/useEidolonStore';
import { PlotlyChart } from './PlotlyChart';

const StatCard: React.FC<{ label: string; value: string | number; sub?: string; accent?: string }> = ({
  label,
  value,
  sub,
  accent = 'text-slate-100',
}) => (
  <div className="panel p-3.5">
    <div className="text-[11px] uppercase tracking-wider text-slate-400">{label}</div>
    <div className={`mt-1 text-xl font-mono font-semibold ${accent}`}>{value}</div>
    {sub && <div className="mt-1 text-[11px] text-slate-500 font-mono">{sub}</div>}
  </div>
);

export const CommandCentre: React.FC = () => {
  const { summary, status, recentEvents, metricsHistory, institutions, communities, locations } =
    useEidolonStore();
  const m = summary?.metrics;

  const ticks = metricsHistory.map((r) => r.tick);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-5 gap-3">
        <StatCard
          label="Population"
          value={m?.population ?? 0}
          sub={`Across ${locations.length} world nodes`}
        />
        <StatCard
          label="Simulation Tick"
          value={summary?.clock.tick ?? 0}
          sub={`${summary?.clock.season ?? 'spring'} • Year ${summary?.clock.year ?? 1}`}
          accent="text-sky-300"
        />
        <StatCard
          label="Cooperation Index"
          value={`${((m?.cooperation_index ?? 0) * 100).toFixed(1)}%`}
          sub={`${summary?.total_cooperations ?? 0} / ${summary?.total_interactions ?? 0} social acts`}
          accent="text-emerald-300"
        />
        <StatCard
          label="Network Density"
          value={(m?.network_density ?? 0).toFixed(4)}
          sub={`Mean Trust ${(m?.mean_trust ?? 0.5).toFixed(3)}`}
          accent="text-violet-300"
        />
        <StatCard
          label="Communities & Inst."
          value={`${m?.community_count ?? 0} / ${m?.institution_count ?? 0}`}
          sub={`Gini ${(m?.gini_coefficient ?? 0).toFixed(3)} • Need ${(
            (m?.avg_need_satisfaction ?? 0) * 100
          ).toFixed(0)}%`}
          accent="text-amber-300"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 panel overflow-hidden">
          <div className="panel-header flex justify-between items-center">
            <span>Live Societal Trajectory (Computed State)</span>
            <span className="font-mono text-[10px] text-slate-400">STATUS: {status.toUpperCase()}</span>
          </div>
          <div className="p-2">
            <PlotlyChart
              height={265}
              data={[
                {
                  x: ticks,
                  y: metricsHistory.map((r) => r.cooperation_index),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Cooperation',
                  line: { color: '#34d399', width: 2 },
                },
                {
                  x: ticks,
                  y: metricsHistory.map((r) => r.mean_trust),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Mean Trust',
                  line: { color: '#38bdf8', width: 2 },
                },
                {
                  x: ticks,
                  y: metricsHistory.map((r) => r.avg_need_satisfaction),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Need Satisfaction',
                  line: { color: '#fbbf24', width: 1.8 },
                },
                {
                  x: ticks,
                  y: metricsHistory.map((r) => r.gini_coefficient),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Gini Inequality',
                  line: { color: '#fb7185', width: 1.6, dash: 'dot' },
                },
              ]}
              layout={{ yaxis: { range: [0, 1], gridcolor: '#1e2631' } }}
            />
          </div>
        </div>

        <div className="panel flex flex-col">
          <div className="panel-header">Economic Market &amp; Environment</div>
          <div className="p-3.5 space-y-3 text-xs flex-1">
            <div className="flex justify-between text-slate-400">
              <span>Available Resources</span>
              <span className="font-mono text-slate-100">{(m?.total_resources ?? 0).toFixed(1)}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Total Trades Settled</span>
              <span className="font-mono text-slate-100">{summary?.economy.total_trades ?? 0}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Last Env Event</span>
              <span className="font-mono text-amber-300 truncate max-w-[180px]">
                {summary?.environment.last_event_summary ?? 'Stable'}
              </span>
            </div>
            <div className="border-t border-[#232a35] pt-2">
              <div className="text-[11px] uppercase text-slate-400 mb-1.5">Scarcity Exchange Prices</div>
              <div className="grid grid-cols-2 gap-1.5 font-mono text-[11px]">
                {Object.entries(summary?.economy.prices || {}).map(([res, price]) => (
                  <div key={res} className="flex justify-between bg-[#0b0d10] px-2 py-1 rounded border border-[#1f2630]">
                    <span className="text-slate-400">{res}</span>
                    <span className="text-sky-300">{Number(price).toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="border-t border-[#232a35] pt-2">
              <div className="text-[11px] uppercase text-slate-400 mb-1">Active Structures</div>
              <div className="text-[11px] text-slate-300 font-mono">
                {communities.length} clusters • {institutions.length} rule-governed institutions
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header flex justify-between">
          <span>Verified Computational Event Stream</span>
          <span className="font-mono text-[10px] text-slate-400">Last {recentEvents.length} events</span>
        </div>
        <div className="max-h-56 overflow-y-auto divide-y divide-[#1b212b] text-xs font-mono">
          {recentEvents.slice(0, 25).map((ev, idx) => (
            <div key={idx} className="px-3.5 py-1.5 flex items-center gap-3 hover:bg-slate-800/30">
              <span className="text-slate-500 w-14">t={ev.tick}</span>
              <span className="text-sky-300 w-36 truncate">{ev.event_type}</span>
              <span className="text-slate-200 w-24 truncate">{ev.actor_id || 'world'}</span>
              <span className="text-slate-400 w-24 truncate">{ev.target_id ? `-> ${ev.target_id}` : ''}</span>
              <span className="text-slate-400 truncate flex-1">{JSON.stringify(ev.payload)}</span>
            </div>
          ))}
          {recentEvents.length === 0 && (
            <div className="px-4 py-6 text-center text-slate-500">
              Step or run the simulation to observe local computational events.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
