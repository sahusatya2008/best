import React, { useState } from 'react';
import { useEidolonStore } from '../store/useEidolonStore';
import type { AgentDetail, DecisionExplanation } from '../types/eidolon';

const ProgressBar: React.FC<{ label: string; value: number; color?: string }> = ({
  label,
  value,
  color = 'bg-sky-400',
}) => (
  <div className="space-y-0.5">
    <div className="flex justify-between text-[11px]">
      <span className="text-slate-400 capitalize">{label.replace(/_/g, ' ')}</span>
      <span className="font-mono text-slate-200">{value.toFixed(2)}</span>
    </div>
    <div className="h-1.5 bg-[#0b0d10] rounded overflow-hidden border border-[#1f2630]">
      <div className={`h-full ${color}`} style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }} />
    </div>
  </div>
);

export const AgentObservatory: React.FC = () => {
  const { agents, selectedAgentId, selectedAgentDetail, selectAgent } = useEidolonStore();
  const [search, setSearch] = useState('');
  const [replayIndex, setReplayIndex] = useState<number | null>(null);

  const agent: AgentDetail | null = selectedAgentDetail?.agent || null;
  const rels: any[] = selectedAgentDetail?.relationships || [];
  const inst: any = selectedAgentDetail?.institution || null;

  const filteredList = agents
    .filter((a) => a.name.toLowerCase().includes(search.toLowerCase()) || a.agent_id.includes(search))
    .slice(0, 80);

  const history: DecisionExplanation[] = agent?.decision_history || [];
  const activeExpl: DecisionExplanation | undefined =
    replayIndex !== null && history[replayIndex] ? history[replayIndex] : agent?.last_explanation;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      <div className="panel flex flex-col max-h-[760px]">
        <div className="panel-header">Agents ({agents.length})</div>
        <div className="p-2 border-b border-[#232a35]">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter by ID or name..."
            className="w-full bg-[#0b0d10] border border-[#232a35] rounded px-2.5 py-1.5 text-xs text-slate-200"
          />
        </div>
        <div className="overflow-y-auto divide-y divide-[#1a2029] text-xs">
          {filteredList.map((ag) => (
            <button
              key={ag.agent_id}
              onClick={() => {
                setReplayIndex(null);
                selectAgent(ag.agent_id);
              }}
              className={`w-full text-left px-3 py-2 flex items-center justify-between hover:bg-slate-800/40 ${
                ag.agent_id === selectedAgentId ? 'bg-sky-500/15 border-l-2 border-l-sky-400' : ''
              }`}
            >
              <div>
                <div className="font-mono text-slate-200">{ag.name}</div>
                <div className="text-[10px] text-slate-400">
                  {ag.occupation} • {ag.last_action}
                </div>
              </div>
              <span className="font-mono text-[11px] text-emerald-300">
                {(ag.mean_need_satisfaction * 100).toFixed(0)}%
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="lg:col-span-3 space-y-4">
        {!agent ? (
          <div className="panel p-8 text-center text-slate-400 text-sm">
            Select an autonomous agent to inspect its cognitive architecture.
          </div>
        ) : (
          <>
            <div className="panel p-4 grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
              <div>
                <div className="text-slate-400">Identity</div>
                <div className="font-mono text-sm font-semibold text-sky-300">{agent.name}</div>
                <div className="font-mono text-[10px] text-slate-500">{agent.agent_id} • Gen {agent.generation}</div>
              </div>
              <div>
                <div className="text-slate-400">Role &amp; Age</div>
                <div className="font-mono text-slate-200 capitalize">{agent.occupation}</div>
                <div className="font-mono text-[10px] text-slate-400">Age {agent.age} • Status {agent.social_status.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-slate-400">Location &amp; Cluster</div>
                <div className="font-mono text-slate-200">{agent.location_id}</div>
                <div className="font-mono text-[10px] text-slate-400">{agent.community_id || 'Independent'}</div>
              </div>
              <div>
                <div className="text-slate-400">Reputation &amp; Wealth</div>
                <div className="font-mono text-emerald-300">Rep {agent.reputation.toFixed(3)}</div>
                <div className="font-mono text-[10px] text-amber-300">Wealth {agent.wealth.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-slate-400">Learning Stats</div>
                <div className="font-mono text-slate-200">{agent.learning_summary.total_updates} Q-updates</div>
                <div className="font-mono text-[10px] text-violet-300">
                  {agent.learning_summary.social_adoptions} social adoptions
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="panel p-3.5 space-y-2">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Big Five Personality Weights
                </div>
                {Object.entries(agent.traits).map(([k, v]) => (
                  <ProgressBar key={k} label={k} value={v} color="bg-violet-400" />
                ))}
                <div className="pt-2 border-t border-[#232a35] text-[11px] space-y-1">
                  <div className="text-slate-400 uppercase">Cultural Traits</div>
                  {Object.entries(agent.cultural_traits).map(([k, v]) => (
                    <div key={k} className="flex justify-between font-mono">
                      <span className="text-slate-400">{k}</span>
                      <span className="text-sky-300">{v}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="panel p-3.5 space-y-2">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Dynamic Internal Needs
                </div>
                {Object.entries(agent.needs).map(([k, v]) => (
                  <ProgressBar
                    key={k}
                    label={k}
                    value={v}
                    color={v > 0.65 ? 'bg-emerald-400' : v > 0.35 ? 'bg-amber-400' : 'bg-rose-400'}
                  />
                ))}
              </div>

              <div className="panel p-3.5 space-y-2.5 text-xs">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Resources, Goals &amp; Institution
                </div>
                <div className="grid grid-cols-2 gap-1.5 font-mono text-[11px]">
                  {Object.entries(agent.resources).map(([r, q]) => (
                    <div key={r} className="flex justify-between bg-[#0b0d10] px-2 py-1 rounded border border-[#1f2630]">
                      <span className="text-slate-400">{r}</span>
                      <span className="text-slate-100">{Number(q).toFixed(2)}</span>
                    </div>
                  ))}
                </div>
                <div className="border-t border-[#232a35] pt-2 space-y-1">
                  <div className="text-[11px] uppercase text-slate-400">Active Goals</div>
                  {agent.goals.map((g) => (
                    <div key={g.goal_id} className="flex justify-between font-mono text-[11px]">
                      <span className="text-slate-300">{g.goal_type}</span>
                      <span className="text-sky-300">{(g.progress * 100).toFixed(0)}% (p={g.priority.toFixed(2)})</span>
                    </div>
                  ))}
                </div>
                {inst && (
                  <div className="border-t border-[#232a35] pt-2 text-[11px] font-mono">
                    <span className="text-slate-400">Institution: </span>
                    <span className="text-emerald-300">{inst.name}</span>
                  </div>
                )}
              </div>
            </div>

            {/* DECISION EXPLAINABILITY & REPLAY */}
            <div className="panel">
              <div className="panel-header flex flex-wrap justify-between items-center gap-2">
                <span>Decision Explainability &amp; Replay</span>
                {history.length > 0 && (
                  <div className="flex items-center gap-2 font-mono text-[11px] normal-case">
                    <span>Replay step:</span>
                    <input
                      type="range"
                      min={0}
                      max={history.length - 1}
                      value={replayIndex ?? history.length - 1}
                      onChange={(e) => setReplayIndex(Number(e.target.value))}
                      className="accent-sky-400"
                    />
                    <span className="text-sky-300">
                      {(replayIndex ?? history.length - 1) + 1}/{history.length}
                    </span>
                  </div>
                )}
              </div>
              {activeExpl && activeExpl.selected_action ? (
                <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  <div className="bg-[#0b0d10] border border-[#232a35] rounded p-3.5 space-y-2">
                    <div className="flex justify-between items-center border-b border-[#1f2630] pb-2">
                      <span className="text-emerald-300 font-bold text-sm uppercase">
                        SELECTED ACTION: {activeExpl.selected_action}
                      </span>
                      <span className="text-slate-400">Tick {activeExpl.tick}</span>
                    </div>
                    <div className="space-y-1">
                      {Object.entries(activeExpl.decision_factors || {}).map(([fk, fv]) => (
                        <div key={fk} className="flex justify-between">
                          <span className="text-slate-400">{fk.replace(/_/g, ' ')}:</span>
                          <span className="text-slate-100">{Number(fv).toFixed(4)}</span>
                        </div>
                      ))}
                    </div>
                    <div className="border-t border-[#1f2630] pt-2 flex justify-between text-sky-300 font-semibold">
                      <span>Selected utility:</span>
                      <span>{Number(activeExpl.selected_utility).toFixed(4)}</span>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="bg-[#0b0d10] border border-[#232a35] rounded p-3 space-y-1.5">
                      <div className="text-slate-400 uppercase text-[11px]">Alternative Actions Evaluated</div>
                      {(activeExpl.alternatives || []).map((alt, i) => (
                        <div key={i} className="flex justify-between">
                          <span className="text-slate-300">{alt.action}</span>
                          <span className="text-amber-300">{Number(alt.utility).toFixed(4)}</span>
                        </div>
                      ))}
                    </div>
                    <div className="bg-[#0b0d10] border border-[#232a35] rounded p-3 space-y-1">
                      <div className="text-slate-400">Mechanism: <span className="text-slate-200">{activeExpl.decision_mechanism}</span></div>
                      <div className="text-slate-400">Urgent Need: <span className="text-rose-300">{activeExpl.most_urgent_need}</span></div>
                      <div className="text-slate-400">Q-State Key: <span className="text-violet-300">{activeExpl.state_key}</span></div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 text-xs text-slate-500">Advance at least 1 simulation tick to inspect decision explanations.</div>
              )}
            </div>

            {/* MEMORY & RELATIONSHIPS */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="panel p-3.5 text-xs space-y-2">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  4-Layer Memory Core (W:{agent.memory_summary.working_count} • E:{agent.memory_summary.episodic_count} • S:{agent.memory_summary.semantic_count} • P:{agent.memory_summary.procedural_count})
                </div>
                <div className="max-h-48 overflow-y-auto divide-y divide-[#1a2029] font-mono text-[11px]">
                  {agent.memory_summary.recent_episodic.map((m, idx) => (
                    <div key={idx} className="py-1.5 flex justify-between">
                      <span className="text-slate-300">t={m.tick} {m.event_type}</span>
                      <span className={m.outcome >= 0 ? 'text-emerald-300' : 'text-rose-300'}>
                        out={m.outcome.toFixed(2)} {m.consolidated ? '★' : ''}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="panel p-3.5 text-xs space-y-2">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Social Ties &amp; Trust ({rels.length})
                </div>
                <div className="max-h-48 overflow-y-auto divide-y divide-[#1a2029] font-mono text-[11px]">
                  {rels.map((r, idx) => {
                    const peer = r.source_id === agent.agent_id ? r.target_id : r.source_id;
                    return (
                      <div key={idx} className="py-1.5 flex justify-between">
                        <span className="text-sky-300">{peer} ({r.rel_type})</span>
                        <span className="text-slate-300">
                          trust={r.trust.toFixed(2)} w={r.weight.toFixed(2)} (n={r.interaction_count})
                        </span>
                      </div>
                    );
                  })}
                  {rels.length === 0 && <div className="text-slate-500 py-2">No social ties recorded yet.</div>}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
