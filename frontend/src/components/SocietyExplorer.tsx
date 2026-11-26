import React, { useMemo, useRef, useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Line, Text } from '@react-three/drei';
import * as THREE from 'three';
import { useEidolonStore } from '../store/useEidolonStore';
import type { AgentSummary, WorldLocation } from '../types/eidolon';

const ACTION_COLORS: Record<string, string> = {
  cooperate: '#34d399',
  trade: '#38bdf8',
  communicate: '#a78bfa',
  compete: '#fb7185',
  harvest_food: '#fbbf24',
  gather_water: '#22d3ee',
  extract_materials: '#f97316',
  craft_tools: '#e879f9',
  research_knowledge: '#60a5fa',
  migrate: '#facc15',
  rest: '#94a3b8',
};

const COMMUNITY_PALETTE = ['#38bdf8', '#34d399', '#fbbf24', '#a78bfa', '#fb7185', '#22d3ee', '#f97316'];

function agentPosition3D(ag: AgentSummary, idx: number, loc: WorldLocation | undefined): [number, number, number] {
  const bx = ((loc?.x ?? 50) - 50) * 0.45;
  const bz = ((loc?.y ?? 50) - 50) * 0.45;
  const angle = (idx * 2.39996) % (Math.PI * 2);
  const radius = 0.8 + ((idx % 7) * 0.28);
  return [bx + Math.cos(angle) * radius, 0.35, bz + Math.sin(angle) * radius];
}

const InstancedAgentsMesh: React.FC<{
  agents: AgentSummary[];
  locMap: Map<string, WorldLocation>;
  colorMode: 'action' | 'community' | 'needs';
  selectedAgentId: string | null;
  onSelect: (id: string) => void;
}> = ({ agents, locMap, colorMode, selectedAgentId, onSelect }) => {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const colorObj = useMemo(() => new THREE.Color(), []);

  useEffect(() => {
    const mesh = meshRef.current;
    if (!mesh) return;
    agents.forEach((ag, idx) => {
      const [x, y, z] = agentPosition3D(ag, idx, locMap.get(ag.location_id));
      const scale = ag.agent_id === selectedAgentId ? 1.7 : 1.0;
      dummy.position.set(x, y, z);
      dummy.scale.set(scale, scale, scale);
      dummy.updateMatrix();
      mesh.setMatrixAt(idx, dummy.matrix);

      let hex = '#94a3b8';
      if (colorMode === 'action') {
        hex = ACTION_COLORS[ag.last_action] || '#94a3b8';
      } else if (colorMode === 'community') {
        if (ag.community_id) {
          const num = parseInt(ag.community_id.replace(/\D/g, ''), 10) || 0;
          hex = COMMUNITY_PALETTE[num % COMMUNITY_PALETTE.length];
        } else {
          hex = '#475569';
        }
      } else {
        const sat = ag.mean_need_satisfaction;
        hex = sat > 0.7 ? '#34d399' : sat > 0.45 ? '#fbbf24' : '#fb7185';
      }
      if (ag.agent_id === selectedAgentId) hex = '#ffffff';
      colorObj.set(hex);
      mesh.setColorAt(idx, colorObj);
    });
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  }, [agents, locMap, colorMode, selectedAgentId, dummy, colorObj]);

  if (agents.length === 0) return null;

  return (
    <instancedMesh
      ref={meshRef}
      args={[undefined, undefined, agents.length]}
      onClick={(e) => {
        e.stopPropagation();
        if (e.instanceId !== undefined && agents[e.instanceId]) {
          onSelect(agents[e.instanceId].agent_id);
        }
      }}
    >
      <sphereGeometry args={[0.28, 10, 10]} />
      <meshStandardMaterial roughness={0.35} metalness={0.15} />
    </instancedMesh>
  );
};

export const SocietyExplorer: React.FC = () => {
  const { agents, locations, communities, selectedAgentId, selectAgent, setActiveTab } = useEidolonStore();
  const [viewMode, setViewMode] = useState<'3d' | '2d'>('3d');
  const [colorMode, setColorMode] = useState<'action' | 'community' | 'needs'>('action');
  const [filterLoc, setFilterLoc] = useState<string>('all');
  const [filterComm, setFilterComm] = useState<string>('all');
  const [showClusters, setShowClusters] = useState<boolean>(true);

  const locMap = useMemo(() => new Map(locations.map((l) => [l.location_id, l])), [locations]);

  const filteredAgents = useMemo(
    () =>
      agents.filter((ag) => {
        if (filterLoc !== 'all' && ag.location_id !== filterLoc) return false;
        if (filterComm !== 'all' && ag.community_id !== filterComm) return false;
        return true;
      }),
    [agents, filterLoc, filterComm]
  );

  const selectedAgent = useMemo(
    () => agents.find((a) => a.agent_id === selectedAgentId) || null,
    [agents, selectedAgentId]
  );

  const edges3D = useMemo(() => {
    const seen = new Set<string>();
    const pairs: Array<[[number, number, number], [number, number, number]]> = [];
    for (const loc of locations) {
      for (const nId of loc.neighbors) {
        const key = loc.location_id < nId ? `${loc.location_id}-${nId}` : `${nId}-${loc.location_id}`;
        if (seen.has(key)) continue;
        seen.add(key);
        const nb = locMap.get(nId);
        if (!nb) continue;
        pairs.push([
          [(loc.x - 50) * 0.45, 0.05, (loc.y - 50) * 0.45],
          [(nb.x - 50) * 0.45, 0.05, (nb.y - 50) * 0.45],
        ]);
      }
    }
    return pairs;
  }, [locations, locMap]);

  return (
    <div className="space-y-4">
      <div className="panel p-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex rounded overflow-hidden border border-[#2d3644]">
            <button
              onClick={() => setViewMode('3d')}
              className={`px-3 py-1 font-mono ${viewMode === '3d' ? 'bg-sky-600 text-white' : 'bg-[#0b0d10] text-slate-400'}`}
            >
              3D WebGL
            </button>
            <button
              onClick={() => setViewMode('2d')}
              className={`px-3 py-1 font-mono ${viewMode === '2d' ? 'bg-sky-600 text-white' : 'bg-[#0b0d10] text-slate-400'}`}
            >
              2D Grid
            </button>
          </div>

          <select
            value={colorMode}
            onChange={(e) => setColorMode(e.target.value as any)}
            className="bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1 text-slate-200"
          >
            <option value="action">Color: Last Action</option>
            <option value="community">Color: Emergent Community</option>
            <option value="needs">Color: Need Satisfaction</option>
          </select>

          <select
            value={filterLoc}
            onChange={(e) => setFilterLoc(e.target.value)}
            className="bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1 text-slate-200"
          >
            <option value="all">All Locations ({locations.length})</option>
            {locations.map((l) => (
              <option key={l.location_id} value={l.location_id}>
                {l.name}
              </option>
            ))}
          </select>

          <select
            value={filterComm}
            onChange={(e) => setFilterComm(e.target.value)}
            className="bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1 text-slate-200"
          >
            <option value="all">All Communities ({communities.length})</option>
            {communities.map((c) => (
              <option key={c.community_id} value={c.community_id}>
                {c.name} ({c.member_count})
              </option>
            ))}
          </select>

          <label className="flex items-center gap-1.5 text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={showClusters}
              onChange={(e) => setShowClusters(e.target.checked)}
              className="accent-sky-500"
            />
            <span>Highlight Clusters</span>
          </label>
        </div>

        <div className="text-xs font-mono text-slate-400">
          Showing {filteredAgents.length} / {agents.length} autonomous agents
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3 panel overflow-hidden relative h-[540px] bg-[#080a0d]">
          {viewMode === '3d' ? (
            <Canvas camera={{ position: [0, 28, 32], fov: 46 }}>
              <color attach="background" args={['#080a0d']} />
              <ambientLight intensity={0.65} />
              <directionalLight position={[15, 30, 15]} intensity={0.9} />
              <gridHelper args={[50, 25, '#1e293b', '#141a23']} />
              <OrbitControls enableDamping dampingFactor={0.08} />

              {edges3D.map((pts, idx) => (
                <Line key={idx} points={pts} color="#283548" lineWidth={1.2} />
              ))}

              {locations.map((loc) => {
                const x = (loc.x - 50) * 0.45;
                const z = (loc.y - 50) * 0.45;
                const totalRes = Object.values(loc.resources).reduce((s, r) => s + r.quantity, 0);
                const pillarH = Math.max(0.4, Math.min(3.5, totalRes / 180));
                const nodeColor =
                  loc.kind === 'settlement'
                    ? '#38bdf8'
                    : loc.kind === 'market'
                    ? '#fbbf24'
                    : loc.kind === 'sanctuary'
                    ? '#a78bfa'
                    : '#34d399';
                return (
                  <group key={loc.location_id} position={[x, 0, z]}>
                    <mesh position={[0, pillarH / 2, 0]}>
                      <cylinderGeometry args={[0.55, 0.7, pillarH, 12]} />
                      <meshStandardMaterial color={nodeColor} opacity={0.45} transparent />
                    </mesh>
                    <Text position={[0, pillarH + 0.55, 0]} fontSize={0.55} color="#cbd5e1" anchorX="center">
                      {loc.name}
                    </Text>
                  </group>
                );
              })}

              {showClusters &&
                communities.map((c, idx) => (
                  <mesh
                    key={c.community_id}
                    position={[(c.centroid_x - 50) * 0.45, 0.04, (c.centroid_y - 50) * 0.45]}
                    rotation={[-Math.PI / 2, 0, 0]}
                  >
                    <ringGeometry args={[2.3, 2.6, 24]} />
                    <meshBasicMaterial color={COMMUNITY_PALETTE[idx % COMMUNITY_PALETTE.length]} transparent opacity={0.45} />
                  </mesh>
                ))}

              <InstancedAgentsMesh
                agents={filteredAgents}
                locMap={locMap}
                colorMode={colorMode}
                selectedAgentId={selectedAgentId}
                onSelect={(id) => selectAgent(id)}
              />
            </Canvas>
          ) : (
            <svg viewBox="0 0 100 100" className="w-full h-full sci-grid-bg">
              {locations.map((loc) =>
                loc.neighbors.map((nid) => {
                  if (loc.location_id >= nid) return null;
                  const nb = locMap.get(nid);
                  if (!nb) return null;
                  return (
                    <line
                      key={`${loc.location_id}-${nid}`}
                      x1={loc.x}
                      y1={100 - loc.y}
                      x2={nb.x}
                      y2={100 - nb.y}
                      stroke="#253042"
                      strokeWidth="0.35"
                    />
                  );
                })
              )}
              {showClusters &&
                communities.map((c, idx) => (
                  <circle
                    key={c.community_id}
                    cx={c.centroid_x}
                    cy={100 - c.centroid_y}
                    r={6.5}
                    fill="none"
                    stroke={COMMUNITY_PALETTE[idx % COMMUNITY_PALETTE.length]}
                    strokeWidth="0.4"
                    strokeDasharray="1.2 0.8"
                    opacity={0.7}
                  />
                ))}
              {locations.map((loc) => (
                <g key={loc.location_id}>
                  <circle cx={loc.x} cy={100 - loc.y} r="2.2" fill="#1e293b" stroke="#38bdf8" strokeWidth="0.4" />
                  <text x={loc.x} y={100 - loc.y - 3.0} fontSize="2.1" fill="#94a3b8" textAnchor="middle">
                    {loc.name}
                  </text>
                </g>
              ))}
              {filteredAgents.map((ag, idx) => {
                const loc = locMap.get(ag.location_id);
                const angle = (idx * 2.39996) % (Math.PI * 2);
                const r = 2.0 + (idx % 6) * 0.55;
                const ax = (loc?.x ?? 50) + Math.cos(angle) * r;
                const ay = 100 - ((loc?.y ?? 50) + Math.sin(angle) * r);
                const fill =
                  colorMode === 'action'
                    ? ACTION_COLORS[ag.last_action] || '#94a3b8'
                    : colorMode === 'needs'
                    ? ag.mean_need_satisfaction > 0.65
                      ? '#34d399'
                      : '#fb7185'
                    : ag.community_id
                    ? COMMUNITY_PALETTE[(parseInt(ag.community_id.replace(/\D/g, ''), 10) || 0) % COMMUNITY_PALETTE.length]
                    : '#475569';
                return (
                  <circle
                    key={ag.agent_id}
                    cx={ax}
                    cy={ay}
                    r={ag.agent_id === selectedAgentId ? 1.1 : 0.65}
                    fill={fill}
                    stroke={ag.agent_id === selectedAgentId ? '#ffffff' : 'none'}
                    strokeWidth="0.3"
                    className="cursor-pointer"
                    onClick={() => selectAgent(ag.agent_id)}
                  />
                );
              })}
            </svg>
          )}
        </div>

        <div className="panel flex flex-col">
          <div className="panel-header">Selected Entity &amp; Legend</div>
          <div className="p-3.5 space-y-3 text-xs flex-1 overflow-y-auto">
            {selectedAgent ? (
              <div className="space-y-2 border-b border-[#232a35] pb-3">
                <div className="flex justify-between items-center">
                  <span className="font-mono font-semibold text-sky-300">{selectedAgent.name}</span>
                  <span className="font-mono text-[10px] text-slate-400">{selectedAgent.agent_id}</span>
                </div>
                <div className="grid grid-cols-2 gap-1.5 text-[11px] font-mono">
                  <div className="text-slate-400">Occupation: <span className="text-slate-200">{selectedAgent.occupation}</span></div>
                  <div className="text-slate-400">Action: <span className="text-emerald-300">{selectedAgent.last_action}</span></div>
                  <div className="text-slate-400">Reputation: <span className="text-slate-200">{selectedAgent.reputation.toFixed(2)}</span></div>
                  <div className="text-slate-400">Needs: <span className="text-amber-300">{(selectedAgent.mean_need_satisfaction * 100).toFixed(0)}%</span></div>
                </div>
                <button
                  onClick={() => setActiveTab('agent')}
                  className="w-full mt-1 py-1.5 rounded bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 border border-sky-500/30 text-xs font-medium"
                >
                  Inspect Cognitive Architecture →
                </button>
              </div>
            ) : (
              <div className="text-slate-500">Click any agent in the 3D/2D world to inspect.</div>
            )}

            <div>
              <div className="text-[11px] uppercase text-slate-400 mb-1.5">Action Color Key</div>
              <div className="grid grid-cols-2 gap-1 text-[11px] font-mono">
                {Object.entries(ACTION_COLORS).map(([act, hex]) => (
                  <div key={act} className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: hex }} />
                    <span className="text-slate-300 truncate">{act}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
