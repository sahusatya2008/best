import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CommandCentre } from '../components/CommandCentre';
import { EmergenceObservatory } from '../components/EmergenceObservatory';
import { AgentObservatory } from '../components/AgentObservatory';
import { useEidolonStore } from '../store/useEidolonStore';

vi.mock('../components/PlotlyChart', () => ({
  PlotlyChart: () => <div data-testid="plotly-mock" />,
}));

describe('EIDOLON Frontend Components', () => {
  beforeEach(() => {
    useEidolonStore.setState({
      status: 'paused',
      summary: {
        experiment_id: 'exp_test',
        config: {
          scenario_id: 'cooperation_experiment',
          name: 'Test Experiment',
          description: '',
          seed: 42,
          population_size: 20,
          num_locations: 8,
          duration_ticks: 100,
          initial_resource_richness: 1.0,
          scarcity: 0.2,
          climate_severity: 0.1,
          regeneration_scale: 1.0,
          env_event_probability: 0.04,
          learning_rate: 0.15,
          discount_factor: 0.9,
          exploration_rate: 0.12,
          social_learning_prob: 0.25,
          adaptation_speed: 1.0,
          memory_capacity: 80,
          cooperation_reward: 0.28,
          social_interaction_prob: 0.85,
          cultural_transmission_rate: 0.28,
          institutions_enabled: true,
          institution_formation_threshold: 0.58,
          personality_means: {},
          personality_std: 0.16,
        },
        clock: { tick: 25, day: 6, season: 'spring', year: 1 },
        environment: {
          climate_severity: 0.1,
          regeneration_scale: 1.0,
          event_probability: 0.04,
          last_event_summary: 'Stable',
          total_natural_events: 0,
        },
        economy: {
          prices: { food: 1.2, water: 1.0 },
          tick_trade_volume: 4.5,
          total_trade_volume: 45.0,
          total_trades: 12,
          total_produced: 200,
          total_consumed: 100,
        },
        metrics: {
          tick: 25,
          population: 20,
          total_resources: 5000,
          cooperation_index: 0.625,
          gini_coefficient: 0.12,
          mean_trust: 0.72,
          network_density: 0.18,
          community_count: 2,
          institution_count: 1,
          cultural_diversity: 0.81,
          mean_q_value: 0.24,
          mean_utility: 0.35,
          trade_volume: 4.5,
          collective_success_rate: 0.9,
          avg_need_satisfaction: 0.78,
        },
        cultural_metrics: {
          cultural_diversity: 0.81,
          sharing_norm_adoption: 0.4,
          collaborative_ethic_rate: 0.35,
          inter_community_divergence: 0.12,
          trait_distributions: {},
        },
        total_interactions: 40,
        total_cooperations: 25,
        total_competitions: 3,
        performance: { last_tick_ms: 4.2, avg_tick_ms: 4.5 },
      },
      locations: [],
      metricsHistory: [],
      emergentPatterns: [
        {
          pattern_id: 'coop',
          category: 'cooperation_clusters',
          title: 'Cooperation Rate Shift',
          measured_claim: 'Measured cooperation frequency shifted from 24.0% to 62.5% over 25 cycles.',
          measurement_method: 'Windowed ratio',
          baseline_value: 0.24,
          current_value: 0.625,
          delta: 0.385,
          confidence_score: 0.92,
          supporting_data: { total_cooperations: 25 },
        },
      ],
      agents: [
        {
          agent_id: 'ag_0001',
          name: 'Aelon-001',
          birth_tick: 0,
          age: 24,
          generation: 1,
          occupation: 'forager',
          social_status: 0.5,
          location_id: 'loc_00',
          community_id: 'comm_001',
          alive: true,
          reputation: 0.75,
          last_action: 'cooperate',
          last_reward: 0.42,
          cumulative_reward: 6.1,
          wealth: 18.4,
          mean_need_satisfaction: 0.81,
          traits: { openness: 0.6, conscientiousness: 0.7, extraversion: 0.6, agreeableness: 0.8, emotional_stability: 0.7 },
          needs: { nutrition: 0.8, energy: 0.8, safety: 0.8, social_connection: 0.7, belonging: 0.7, achievement: 0.6, knowledge_acquisition: 0.6, resource_security: 0.7 },
          cultural_traits: { sharing_norm: 'generous' },
        },
      ],
      selectedAgentId: 'ag_0001',
      selectedAgentDetail: {
        agent: {
          agent_id: 'ag_0001',
          name: 'Aelon-001',
          birth_tick: 0,
          age: 24,
          generation: 1,
          occupation: 'forager',
          social_status: 0.5,
          location_id: 'loc_00',
          home_location_id: 'loc_00',
          community_id: 'comm_001',
          alive: true,
          reputation: 0.75,
          last_action: 'cooperate',
          last_reward: 0.42,
          cumulative_reward: 6.1,
          wealth: 18.4,
          mean_need_satisfaction: 0.81,
          traits: { openness: 0.6, conscientiousness: 0.7, extraversion: 0.6, agreeableness: 0.8, emotional_stability: 0.7 },
          needs: { nutrition: 0.8, energy: 0.8, safety: 0.8, social_connection: 0.7, belonging: 0.7, achievement: 0.6, knowledge_acquisition: 0.6, resource_security: 0.7 },
          cultural_traits: { sharing_norm: 'generous' },
          resources: { food: 3.0, water: 2.5 },
          goals: [{ goal_id: 'g1', goal_type: 'survive', target_value: 0.85, priority: 0.9, progress: 0.8, active: true }],
          beliefs: {},
          memory_summary: { working_count: 5, episodic_count: 15, semantic_count: 2, procedural_count: 4, recent_episodic: [], semantic: {}, procedural: {} },
          learning_summary: { total_updates: 15, social_adoptions: 2, mean_q_value: 0.24, failure_counts: {}, recent_records: [] },
          last_explanation: {
            tick: 25,
            selected_action: 'cooperate',
            selected_utility: 0.79,
            decision_mechanism: 'Weighted utility selection',
            decision_factors: { social_benefit: 0.91, need_satisfaction: 0.67 },
            alternatives: [{ action: 'trade', utility: 0.63 }],
            state_key: 'nutrition|low|social|rested',
            most_urgent_need: 'achievement',
          },
          decision_history: [],
        },
        relationships: [],
        institution: null,
      },
      refreshMetricsAndEmergence: vi.fn(),
    });
  });

  it('renders CommandCentre with live computed cooperation metrics', () => {
    render(<CommandCentre />);
    expect(screen.getByText('62.5%')).toBeInTheDocument();
    expect(screen.getByText('25 / 40 social acts')).toBeInTheDocument();
  });

  it('renders EmergenceObservatory with measured pattern evidence', () => {
    render(<EmergenceObservatory />);
    expect(screen.getByText('Cooperation Rate Shift')).toBeInTheDocument();
    expect(screen.getByText(/Windowed ratio/)).toBeInTheDocument();
  });

  it('renders AgentObservatory decision explainability panel', () => {
    render(<AgentObservatory />);
    expect(screen.getByText(/SELECTED ACTION: cooperate/i)).toBeInTheDocument();
    expect(screen.getByText('0.7900')).toBeInTheDocument();
  });
});
