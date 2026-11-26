import { create } from 'zustand';
import { api } from '../api/client';
import type {
  AgentDetail,
  AgentSummary,
  CommunityInfo,
  EmergentPattern,
  InstitutionInfo,
  MetricRow,
  SimulationSummary,
  TabId,
  WorldLocation,
} from '../types/eidolon';

interface EidolonStore {
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;

  status: string;
  tickIntervalMs: number;
  summary: SimulationSummary | null;
  locations: WorldLocation[];
  agents: AgentSummary[];
  communities: CommunityInfo[];
  institutions: InstitutionInfo[];
  recentEvents: any[];
  metricsHistory: MetricRow[];
  emergentPatterns: EmergentPattern[];
  scenarios: any[];
  experiments: any[];
  snapshots: any[];
  diagnostics: any | null;
  selectedAgentId: string | null;
  selectedAgentDetail: any | null;
  wsConnected: boolean;
  error: string | null;

  fetchAll: () => Promise<void>;
  refreshMetricsAndEmergence: () => Promise<void>;
  selectAgent: (agentId: string) => Promise<void>;
  stepSimulation: (steps: number) => Promise<void>;
  runSimulation: (tickIntervalMs?: number) => Promise<void>;
  pauseSimulation: () => Promise<void>;
  stopSimulation: () => Promise<void>;
  connectWebSocket: () => () => void;
}

export const useEidolonStore = create<EidolonStore>((set, get) => ({
  activeTab: 'command',
  setActiveTab: (tab) => set({ activeTab: tab }),

  status: 'paused',
  tickIntervalMs: 100,
  summary: null,
  locations: [],
  agents: [],
  communities: [],
  institutions: [],
  recentEvents: [],
  metricsHistory: [],
  emergentPatterns: [],
  scenarios: [],
  experiments: [],
  snapshots: [],
  diagnostics: null,
  selectedAgentId: null,
  selectedAgentDetail: null,
  wsConnected: false,
  error: null,

  fetchAll: async () => {
    try {
      const [stateRes, agentsRes, metricsRes, scenariosRes, expsRes, snapsRes] = await Promise.all([
        api.getState(),
        api.getAgents({ limit: 500 }),
        api.getMetrics(),
        api.getScenarios(),
        api.getExperiments(),
        api.getSnapshots(),
      ]);
      set({
        status: stateRes.status,
        tickIntervalMs: stateRes.tick_interval_ms,
        summary: stateRes.summary,
        locations: stateRes.locations,
        institutions: stateRes.institutions || [],
        communities: stateRes.communities || [],
        recentEvents: stateRes.recent_events || [],
        agents: agentsRes.agents || [],
        metricsHistory: metricsRes.metrics || [],
        scenarios: scenariosRes.scenarios || [],
        experiments: expsRes.experiments || [],
        snapshots: snapsRes.snapshots || [],
        error: null,
      });
      if (!get().selectedAgentId && agentsRes.agents?.length) {
        await get().selectAgent(agentsRes.agents[0].agent_id);
      }
    } catch (e: any) {
      set({ error: e?.message || 'Failed to load simulation state' });
    }
  },

  refreshMetricsAndEmergence: async () => {
    try {
      const [mRes, eRes, dRes] = await Promise.all([
        api.getMetrics(),
        api.getEmergence(),
        api.getDiagnostics(),
      ]);
      set({
        metricsHistory: mRes.metrics || [],
        emergentPatterns: eRes.patterns || [],
        diagnostics: dRes,
      });
    } catch {
      // silent during polling
    }
  },

  selectAgent: async (agentId: string) => {
    set({ selectedAgentId: agentId });
    try {
      const detail = await api.getAgentDetail(agentId);
      set({ selectedAgentDetail: detail });
    } catch (e: any) {
      set({ error: e?.message });
    }
  },

  stepSimulation: async (steps: number) => {
    await api.stepSimulation(steps);
    await get().fetchAll();
    await get().refreshMetricsAndEmergence();
    const sel = get().selectedAgentId;
    if (sel) await get().selectAgent(sel);
  },

  runSimulation: async (tickIntervalMs?: number) => {
    const ms = tickIntervalMs ?? get().tickIntervalMs;
    await api.runSimulation({ tick_interval_ms: ms });
    set({ status: 'running', tickIntervalMs: ms });
  },

  pauseSimulation: async () => {
    await api.pauseSimulation();
    await get().fetchAll();
    await get().refreshMetricsAndEmergence();
  },

  stopSimulation: async () => {
    await api.stopSimulation();
    await get().fetchAll();
    await get().refreshMetricsAndEmergence();
  },

  connectWebSocket: () => {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/ws/simulation`;
    let ws: WebSocket | null = null;
    let alive = true;

    const open = () => {
      if (!alive) return;
      ws = new WebSocket(wsUrl);
      ws.onopen = () => set({ wsConnected: true });
      ws.onclose = () => {
        set({ wsConnected: false });
        if (alive) setTimeout(open, 2000);
      };
      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          if (msg.type === 'tick_update' || msg.type === 'initial_state') {
            set((prev) => {
              const latestMetric = msg.summary?.metrics;
              const nextHist =
                latestMetric && msg.type === 'tick_update'
                  ? [...prev.metricsHistory.filter((m) => m.tick !== latestMetric.tick), latestMetric]
                  : prev.metricsHistory;
              // Merge lightweight agent stream into existing agent records
              let nextAgents = prev.agents;
              if (Array.isArray(msg.agents) && msg.agents.length > 0) {
                const byId = new Map<string, any>(msg.agents.map((a: any) => [a.agent_id, a]));
                nextAgents = prev.agents.map((ag) => {
                  const u = byId.get(ag.agent_id);
                  return u ? { ...ag, ...u } : ag;
                });
                if (nextAgents.length === 0) nextAgents = msg.agents;
              }
              return {
                status: msg.status || prev.status,
                summary: msg.summary || prev.summary,
                locations: msg.locations || prev.locations,
                agents: nextAgents,
                metricsHistory: nextHist,
              };
            });
          }
        } catch {
          // ignore malformed frames
        }
      };
    };

    open();
    return () => {
      alive = false;
      ws?.close();
    };
  },
}));
