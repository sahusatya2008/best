import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useEidolonStore } from '../store/useEidolonStore';

const REL_COLORS: Record<string, string> = {
  cooperation: '#34d399',
  friendship: '#38bdf8',
  mentorship: '#a78bfa',
  rivalry: '#fb7185',
  family: '#fbbf24',
  affiliation: '#94a3b8',
};

export const SocialNetworkObservatory: React.FC = () => {
  const { summary, selectAgent, setActiveTab } = useEidolonStore();
  const [data, setData] = useState<any | null>(null);
  const [minTrust, setMinTrust] = useState(0.0);

  const load = async () => {
    try {
      const res = await api.getSocialNetwork();
      setData(res);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    load();
  }, [summary?.clock.tick]);

  const nodes: any[] = data?.nodes || [];
  const edges: any[] = (data?.edges || []).filter((e: any) => e.trust >= minTrust);
  const analytics = data?.analytics;
  const communities: any[] = data?.communities || [];
  const institutions: any[] = data?.institutions || [];

  const nodePos = new Map<string, { x: number; y: number }>();
  nodes.forEach((n, idx) => {
    const angle = (idx * 2.39996) % (Math.PI * 2);
    const r = 1.8 + (idx % 6) * 0.65;
    nodePos.set(n.agent_id, {
      x: Math.max(4, Math.min(96, n.x + Math.cos(angle) * r)),
      y: Math.max(4, Math.min(96, 100 - (n.y + Math.sin(angle) * r))),
    });
  });

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="panel p-3">
          <div className="text-[11px] uppercase text-slate-400">Active Edges</div>
          <div className="font-mono text-lg text-sky-300">{analytics?.edges ?? 0}</div>
        </div>
        <div className="panel p-3">
          <div className="text-[11px] uppercase text-slate-400">Network Density</div>
          <div className="font-mono text-lg text-emerald-300">{(analytics?.density ?? 0).toFixed(4)}</div>
        </div>
        <div className="panel p-3">
          <div className="text-[11px] uppercase text-slate-400">Clustering Coeff.</div>
          <div className="font-mono text-lg text-violet-300">{(analytics?.clustering_coefficient ?? 0).toFixed(4)}</div>
        </div>
        <div className="panel p-3">
          <div className="text-[11px] uppercase text-slate-400">Mean Degree</div>
          <div className="font-mono text-lg text-amber-300">{(analytics?.mean_degree ?? 0).toFixed(2)}</div>
        </div>
        <div className="panel p-3">
          <div className="text-[11px] uppercase text-slate-400">Clusters / Inst.</div>
          <div className="font-mono text-lg text-slate-100">{communities.length} / {institutions.length}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 panel flex flex-col">
          <div className="panel-header flex justify-between items-center">
            <span>Social Relationship &amp; Trust Topology</span>
            <label className="flex items-center gap-2 font-mono text-[11px] normal-case">
              <span>Min Trust: {minTrust.toFixed(2)}</span>
              <input
                type="range"
                min={0}
                max={0.95}
                step={0.05}
                value={minTrust}
                onChange={(e) => setMinTrust(Number(e.target.value))}
                className="accent-sky-400"
              />
            </label>
          </div>
          <div className="h-[440px] bg-[#080a0d] p-2">
            <svg viewBox="0 0 100 100" className="w-full h-full sci-grid-bg">
              {edges.map((e, i) => {
                const a = nodePos.get(e.source_id);
                const b = nodePos.get(e.target_id);
                if (!a || !b) return null;
                return (
                  <line
                    key={i}
                    x1={a.x}
                    y1={a.y}
                    x2={b.x}
                    y2={b.y}
                    stroke={REL_COLORS[e.rel_type] || '#64748b'}
                    strokeWidth={0.12 + e.weight * 0.35}
                    opacity={0.25 + e.trust * 0.55}
                  />
                );
              })}
              {nodes.map((n) => {
                const p = nodePos.get(n.agent_id);
                if (!p) return null;
                return (
                  <circle
                    key={n.agent_id}
                    cx={p.x}
                    cy={p.y}
                    r={0.55 + n.reputation * 0.45}
                    fill={n.community_id ? '#38bdf8' : '#94a3b8'}
                    className="cursor-pointer"
                    onClick={() => {
                      selectAgent(n.agent_id);
                      setActiveTab('agent');
                    }}
                  >
                    <title>{`${n.name} (rep=${n.reputation})`}</title>
                  </circle>
                );
              })}
            </svg>
          </div>
        </div>

        <div className="space-y-4">
          <div className="panel p-3.5 text-xs space-y-2">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Top Centrality (NetworkX)
            </div>
            <div className="space-y-1 font-mono text-[11px]">
              {(analytics?.top_degree_centrality || []).slice(0, 6).map((item: any) => (
                <div key={item.agent_id} className="flex justify-between">
                  <button
                    onClick={() => {
                      selectAgent(item.agent_id);
                      setActiveTab('agent');
                    }}
                    className="text-sky-300 hover:underline"
                  >
                    {item.name}
                  </button>
                  <span className="text-slate-300">deg={item.value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel p-3.5 text-xs space-y-2">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Emergent Institutions ({institutions.length})
            </div>
            <div className="max-h-56 overflow-y-auto space-y-2">
              {institutions.map((inst: any) => (
                <div key={inst.institution_id} className="bg-[#0b0d10] border border-[#232a35] rounded p-2.5 space-y-1 font-mono text-[11px]">
                  <div className="flex justify-between text-emerald-300 font-semibold">
                    <span>{inst.name}</span>
                    <span>{inst.member_count} members</span>
                  </div>
                  <div className="text-slate-400">
                    Type: {inst.inst_type} • Stability: {inst.stability.toFixed(2)} • Compliance: {(inst.compliance_rate * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
              {institutions.length === 0 && (
                <div className="text-slate-500">Institutions form organically once co-located agents establish repeated mutual trust.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
