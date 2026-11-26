import React, { useEffect, useState } from 'react';
import { Copy, Play, Plus, Trash2 } from 'lucide-react';
import { api } from '../api/client';
import { useEidolonStore } from '../store/useEidolonStore';

export const ResearchLaboratory: React.FC = () => {
  const { summary, scenarios, experiments, fetchAll, runSimulation, pauseSimulation, stepSimulation } =
    useEidolonStore();
  const cfg = summary?.config;

  const [form, setForm] = useState({
    scenario_id: 'cooperation_experiment',
    name: 'Custom Experiment',
    seed: 42,
    population_size: 100,
    duration_ticks: 300,
    scarcity: 0.18,
    initial_resource_richness: 1.0,
    cooperation_reward: 0.28,
    learning_rate: 0.15,
    exploration_rate: 0.12,
    discount_factor: 0.90,
    social_learning_prob: 0.25,
    cultural_transmission_rate: 0.28,
    climate_severity: 0.10,
    institutions_enabled: true,
    agreeableness: 0.56,
    openness: 0.52,
  });

  useEffect(() => {
    if (cfg) {
      setForm({
        scenario_id: cfg.scenario_id,
        name: `${cfg.name}`,
        seed: cfg.seed,
        population_size: cfg.population_size,
        duration_ticks: cfg.duration_ticks,
        scarcity: cfg.scarcity,
        initial_resource_richness: cfg.initial_resource_richness,
        cooperation_reward: cfg.cooperation_reward,
        learning_rate: cfg.learning_rate,
        exploration_rate: cfg.exploration_rate,
        discount_factor: cfg.discount_factor,
        social_learning_prob: cfg.social_learning_prob,
        cultural_transmission_rate: cfg.cultural_transmission_rate,
        climate_severity: cfg.climate_severity,
        institutions_enabled: cfg.institutions_enabled,
        agreeableness: cfg.personality_means?.agreeableness ?? 0.56,
        openness: cfg.personality_means?.openness ?? 0.52,
      });
    }
  }, [cfg?.scenario_id, summary?.experiment_id]);

  const handleCreate = async () => {
    await api.createExperiment({
      scenario_id: form.scenario_id,
      name: form.name,
      seed: Number(form.seed),
      population_size: Number(form.population_size),
      duration_ticks: Number(form.duration_ticks),
      config_overrides: {
        scarcity: Number(form.scarcity),
        initial_resource_richness: Number(form.initial_resource_richness),
        cooperation_reward: Number(form.cooperation_reward),
        learning_rate: Number(form.learning_rate),
        exploration_rate: Number(form.exploration_rate),
        discount_factor: Number(form.discount_factor),
        social_learning_prob: Number(form.social_learning_prob),
        cultural_transmission_rate: Number(form.cultural_transmission_rate),
        climate_severity: Number(form.climate_severity),
        institutions_enabled: Boolean(form.institutions_enabled),
        personality_means: {
          ...(cfg?.personality_means || {}),
          agreeableness: Number(form.agreeableness),
          openness: Number(form.openness),
        },
      },
    });
    await fetchAll();
  };

  const handleApplyLive = async () => {
    await api.patchConfig({
      cooperation_reward: Number(form.cooperation_reward),
      learning_rate: Number(form.learning_rate),
      exploration_rate: Number(form.exploration_rate),
      discount_factor: Number(form.discount_factor),
      social_learning_prob: Number(form.social_learning_prob),
      cultural_transmission_rate: Number(form.cultural_transmission_rate),
      climate_severity: Number(form.climate_severity),
      institutions_enabled: Boolean(form.institutions_enabled),
    });
    await fetchAll();
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 panel">
        <div className="panel-header flex justify-between items-center">
          <span>Experiment Parameter Configuration</span>
          <div className="flex gap-2">
            <button
              onClick={handleApplyLive}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-sky-300 text-[11px] font-mono border border-[#2d3644]"
            >
              Patch Active Run
            </button>
            <button
              onClick={handleCreate}
              className="flex items-center gap-1 px-3 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white text-[11px] font-medium"
            >
              <Plus className="w-3.5 h-3.5" /> Launch New Experiment
            </button>
          </div>
        </div>

        <div className="p-4 grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
          <label className="space-y-1 col-span-2 md:col-span-1">
            <span className="text-slate-400">Scenario Preset</span>
            <select
              value={form.scenario_id}
              onChange={(e) => {
                const sc = scenarios.find((s) => s.scenario_id === e.target.value);
                if (sc) {
                  setForm((f) => ({
                    ...f,
                    scenario_id: sc.scenario_id,
                    name: sc.config.name,
                    seed: sc.config.seed,
                    population_size: sc.config.population_size,
                    scarcity: sc.config.scarcity,
                    cooperation_reward: sc.config.cooperation_reward,
                    climate_severity: sc.config.climate_severity,
                    cultural_transmission_rate: sc.config.cultural_transmission_rate,
                  }));
                }
              }}
              className="w-full bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1.5 text-slate-200"
            >
              {scenarios.map((s) => (
                <option key={s.scenario_id} value={s.scenario_id}>
                  {s.title}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-1">
            <span className="text-slate-400">Experiment Name</span>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1.5 text-slate-200"
            />
          </label>

          <label className="space-y-1">
            <span className="text-slate-400">Random Seed</span>
            <input
              type="number"
              value={form.seed}
              onChange={(e) => setForm({ ...form, seed: Number(e.target.value) })}
              className="w-full bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1.5 font-mono text-slate-200"
            />
          </label>

          {[
            ['population_size', 'Population Size', 10, 2000, 10],
            ['duration_ticks', 'Duration (Ticks)', 20, 5000, 20],
            ['scarcity', 'Resource Scarcity', 0, 0.9, 0.05],
            ['initial_resource_richness', 'Initial Richness', 0.2, 2.5, 0.1],
            ['cooperation_reward', 'Cooperation Synergy', 0, 1.0, 0.02],
            ['learning_rate', 'Learning Rate (α)', 0.01, 0.9, 0.02],
            ['discount_factor', 'Discount Factor (γ)', 0.1, 0.99, 0.02],
            ['exploration_rate', 'Exploration (ε)', 0, 0.6, 0.02],
            ['social_learning_prob', 'Social Learning Prob', 0, 1.0, 0.05],
            ['cultural_transmission_rate', 'Cultural Transmission', 0, 1.0, 0.05],
            ['climate_severity', 'Climate Severity', 0, 1.0, 0.05],
            ['agreeableness', 'Mean Agreeableness', 0.1, 0.95, 0.05],
            ['openness', 'Mean Openness', 0.1, 0.95, 0.05],
          ].map(([key, label, min, max, step]) => (
            <label key={String(key)} className="space-y-1">
              <span className="text-slate-400 flex justify-between">
                <span>{label}</span>
                <span className="font-mono text-sky-300">{(form as any)[key]}</span>
              </span>
              <input
                type="number"
                min={Number(min)}
                max={Number(max)}
                step={Number(step)}
                value={(form as any)[key]}
                onChange={(e) => setForm({ ...form, [key as string]: Number(e.target.value) })}
                className="w-full bg-[#0b0d10] border border-[#232a35] rounded px-2 py-1.5 font-mono text-slate-200"
              />
            </label>
          ))}

          <label className="flex items-center gap-2 pt-5 cursor-pointer">
            <input
              type="checkbox"
              checked={form.institutions_enabled}
              onChange={(e) => setForm({ ...form, institutions_enabled: e.target.checked })}
              className="accent-sky-500"
            />
            <span className="text-slate-200">Institutions Enabled</span>
          </label>
        </div>

        <div className="px-4 pb-4 flex flex-wrap gap-2 border-t border-[#232a35] pt-3">
          <button
            onClick={() => runSimulation()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs"
          >
            <Play className="w-3.5 h-3.5" /> Run Active
          </button>
          <button
            onClick={() => pauseSimulation()}
            className="px-3 py-1.5 rounded bg-amber-600 hover:bg-amber-500 text-white text-xs"
          >
            Pause
          </button>
          <button
            onClick={() => stepSimulation(10)}
            className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono border border-[#2d3644]"
          >
            Step +10
          </button>
          <button
            onClick={() => stepSimulation(50)}
            className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono border border-[#2d3644]"
          >
            Step +50
          </button>
        </div>
      </div>

      <div className="panel flex flex-col max-h-[600px]">
        <div className="panel-header">Saved Experiments ({experiments.length})</div>
        <div className="overflow-y-auto divide-y divide-[#1a2029] text-xs">
          {experiments.map((exp) => {
            const active = exp.id === summary?.experiment_id;
            return (
              <div
                key={exp.id}
                className={`p-3 space-y-1.5 ${active ? 'bg-sky-500/10 border-l-2 border-l-sky-400' : ''}`}
              >
                <div className="flex justify-between items-center">
                  <button
                    onClick={async () => {
                      await api.selectExperiment(exp.id);
                      await fetchAll();
                    }}
                    className="font-semibold text-slate-200 hover:text-sky-300 text-left truncate"
                  >
                    {exp.name}
                  </button>
                  <span className="font-mono text-[10px] text-slate-400">t={exp.current_tick}</span>
                </div>
                <div className="font-mono text-[10px] text-slate-400 flex justify-between">
                  <span>seed={exp.seed} • pop={exp.config?.population_size}</span>
                  <div className="flex gap-2">
                    <button
                      onClick={async () => {
                        await api.duplicateExperiment(exp.id, { seed: exp.seed + 1 });
                        await fetchAll();
                      }}
                      title="Duplicate Experiment"
                      className="text-sky-400 hover:text-sky-300"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={async () => {
                        await api.deleteExperiment(exp.id);
                        await fetchAll();
                      }}
                      title="Delete Experiment"
                      className="text-rose-400 hover:text-rose-300"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
