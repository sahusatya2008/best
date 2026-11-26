export type TabId =
  | 'command'
  | 'explorer'
  | 'agent'
  | 'network'
  | 'lab'
  | 'emergence'
  | 'analytics'
  | 'scenarios'
  | 'compare'
  | 'diagnostics';

export interface MetricRow {
  tick: number;
  population: number;
  total_resources: number;
  cooperation_index: number;
  gini_coefficient: number;
  mean_trust: number;
  network_density: number;
  community_count: number;
  institution_count: number;
  cultural_diversity: number;
  mean_q_value: number;
  mean_utility: number;
  trade_volume: number;
  collective_success_rate: number;
  avg_need_satisfaction: number;
}

export interface ExperimentConfig {
  scenario_id: string;
  name: string;
  description: string;
  seed: number;
  population_size: number;
  num_locations: number;
  duration_ticks: number;
  initial_resource_richness: number;
  scarcity: number;
  climate_severity: number;
  regeneration_scale: number;
  env_event_probability: number;
  learning_rate: number;
  discount_factor: number;
  exploration_rate: number;
  social_learning_prob: number;
  adaptation_speed: number;
  memory_capacity: number;
  cooperation_reward: number;
  social_interaction_prob: number;
  cultural_transmission_rate: number;
  institutions_enabled: boolean;
  institution_formation_threshold: number;
  personality_means: Record<string, number>;
  personality_std: number;
}

export interface SimulationSummary {
  experiment_id: string;
  config: ExperimentConfig;
  clock: {
    tick: number;
    day: number;
    season: string;
    year: number;
  };
  environment: {
    climate_severity: number;
    regeneration_scale: number;
    event_probability: number;
    last_event_summary: string;
    total_natural_events: number;
  };
  economy: {
    prices: Record<string, number>;
    tick_trade_volume: number;
    total_trade_volume: number;
    total_trades: number;
    total_produced: number;
    total_consumed: number;
  };
  metrics: MetricRow;
  cultural_metrics: {
    cultural_diversity: number;
    sharing_norm_adoption: number;
    collaborative_ethic_rate: number;
    inter_community_divergence: number;
    trait_distributions: Record<string, Record<string, number>>;
  };
  total_interactions: number;
  total_cooperations: number;
  total_competitions: number;
  performance: {
    last_tick_ms: number;
    avg_tick_ms: number;
  };
}

export interface LocationResource {
  resource_type: string;
  quantity: number;
  max_capacity: number;
  regen_rate: number;
}

export interface WorldLocation {
  location_id: string;
  name: string;
  region: string;
  kind: string;
  x: number;
  y: number;
  fertility: number;
  hazard_level: number;
  capacity: number;
  neighbors: string[];
  resources: Record<string, LocationResource>;
}

export interface AgentSummary {
  agent_id: string;
  name: string;
  birth_tick: number;
  age: number;
  generation: number;
  occupation: string;
  social_status: number;
  location_id: string;
  community_id: string | null;
  alive: boolean;
  reputation: number;
  last_action: string;
  last_reward: number;
  cumulative_reward: number;
  wealth: number;
  mean_need_satisfaction: number;
  traits: Record<string, number>;
  needs: Record<string, number>;
  cultural_traits: Record<string, string>;
}

export interface DecisionExplanation {
  tick: number;
  selected_action: string;
  selected_utility: number;
  decision_mechanism: string;
  decision_factors: Record<string, number>;
  alternatives: Array<{ action: string; utility: number }>;
  state_key: string;
  most_urgent_need: string;
}

export interface AgentDetail extends AgentSummary {
  home_location_id: string;
  resources: Record<string, number>;
  goals: Array<{
    goal_id: string;
    goal_type: string;
    target_value: number;
    priority: number;
    progress: number;
    active: boolean;
  }>;
  beliefs: Record<string, { belief_key: string; value: number; confidence: number; updated_tick: number }>;
  memory_summary: {
    working_count: number;
    episodic_count: number;
    semantic_count: number;
    procedural_count: number;
    recent_episodic: Array<{
      tick: number;
      event_type: string;
      outcome: number;
      emotional_significance: number;
      recall_count: number;
      consolidated: boolean;
    }>;
    semantic: Record<string, { value: any; confidence: number; updated_tick: number }>;
    procedural: Record<string, { action: string; successes: number; failures: number; avg_outcome: number }>;
  };
  learning_summary: {
    total_updates: number;
    social_adoptions: number;
    mean_q_value: number;
    failure_counts: Record<string, number>;
    recent_records: Array<{
      tick: number;
      state_key: string;
      action: string;
      q_value: number;
      reward: number;
      td_error: number;
      source: string;
    }>;
  };
  last_explanation: DecisionExplanation;
  decision_history: DecisionExplanation[];
}

export interface CommunityInfo {
  community_id: string;
  name: string;
  founded_tick: number;
  member_ids: string[];
  member_count: number;
  cohesion: number;
  centroid_x: number;
  centroid_y: number;
}

export interface InstitutionInfo {
  institution_id: string;
  name: string;
  inst_type: string;
  founder_id: string;
  founded_tick: number;
  location_id: string;
  stability: number;
  treasury: Record<string, number>;
  rules: Record<string, number>;
  member_count: number;
  compliance_rate: number;
  active: boolean;
}

export interface EmergentPattern {
  pattern_id: string;
  category: string;
  title: string;
  measured_claim: string;
  measurement_method: string;
  baseline_value: number;
  current_value: number;
  delta: number;
  confidence_score: number;
  supporting_data: Record<string, any>;
}
