async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getState: () => request<any>('/api/simulation/state'),
  getScenarios: () => request<any>('/api/scenarios'),
  getExperiments: () => request<any>('/api/experiments'),
  createExperiment: (payload: any) =>
    request<any>('/api/experiments', { method: 'POST', body: JSON.stringify(payload) }),
  selectExperiment: (id: string) =>
    request<any>(`/api/experiments/${id}/select`, { method: 'POST' }),
  duplicateExperiment: (id: string, payload: any) =>
    request<any>(`/api/experiments/${id}/duplicate`, { method: 'POST', body: JSON.stringify(payload) }),
  deleteExperiment: (id: string) =>
    request<any>(`/api/experiments/${id}`, { method: 'DELETE' }),
  importExperiment: (payload: any) =>
    request<any>('/api/experiments/import', { method: 'POST', body: JSON.stringify(payload) }),

  runSimulation: (payload: { experiment_id?: string; tick_interval_ms?: number }) =>
    request<any>('/api/simulation/run', { method: 'POST', body: JSON.stringify(payload) }),
  pauseSimulation: () => request<any>('/api/simulation/pause', { method: 'POST' }),
  stopSimulation: () => request<any>('/api/simulation/stop', { method: 'POST' }),
  stepSimulation: (steps = 1) =>
    request<any>('/api/simulation/step', { method: 'POST', body: JSON.stringify({ steps }) }),
  patchConfig: (payload: Record<string, any>) =>
    request<any>('/api/simulation/config', { method: 'PATCH', body: JSON.stringify(payload) }),

  getAgents: (params?: { location_id?: string; community_id?: string; occupation?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.location_id) q.set('location_id', params.location_id);
    if (params?.community_id) q.set('community_id', params.community_id);
    if (params?.occupation) q.set('occupation', params.occupation);
    if (params?.limit) q.set('limit', String(params.limit));
    return request<any>(`/api/agents?${q.toString()}`);
  },
  getAgentDetail: (agentId: string) => request<any>(`/api/agents/${agentId}`),
  getSocialNetwork: () => request<any>('/api/social/network'),
  getMetrics: () => request<any>('/api/analytics/metrics'),
  getEmergence: () => request<any>('/api/analytics/emergence'),
  compareExperiments: (payload: any) =>
    request<any>('/api/analytics/compare', { method: 'POST', body: JSON.stringify(payload) }),
  exportExperiment: () => request<any>('/api/analytics/export', { method: 'POST' }),

  getSnapshots: (experimentId?: string) =>
    request<any>(experimentId ? `/api/snapshots?experiment_id=${experimentId}` : '/api/snapshots'),
  createSnapshot: (label: string) =>
    request<any>('/api/snapshots', { method: 'POST', body: JSON.stringify({ label }) }),
  restoreSnapshot: (snapshotId: string) =>
    request<any>(`/api/snapshots/${snapshotId}/restore`, { method: 'POST' }),
  createBackup: () => request<any>('/api/backups', { method: 'POST' }),
  getDiagnostics: () => request<any>('/api/diagnostics'),
};
