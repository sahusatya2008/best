PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    scenario_id TEXT NOT NULL,
    seed INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    current_tick INTEGER NOT NULL DEFAULT 0,
    config_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS simulation_snapshots (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    tick INTEGER NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    state_blob BLOB NOT NULL,
    checksum TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_snapshots_exp_tick ON simulation_snapshots(experiment_id, tick);

CREATE TABLE IF NOT EXISTS locations (
    experiment_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    kind TEXT NOT NULL,
    x REAL NOT NULL,
    y REAL NOT NULL,
    fertility REAL NOT NULL,
    hazard_level REAL NOT NULL,
    capacity INTEGER NOT NULL,
    PRIMARY KEY (experiment_id, location_id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS location_resources (
    experiment_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    quantity REAL NOT NULL,
    max_capacity REAL NOT NULL,
    regen_rate REAL NOT NULL,
    PRIMARY KEY (experiment_id, location_id, resource_type),
    FOREIGN KEY (experiment_id, location_id) REFERENCES locations(experiment_id, location_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agents (
    experiment_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    name TEXT NOT NULL,
    birth_tick INTEGER NOT NULL,
    age INTEGER NOT NULL,
    generation INTEGER NOT NULL,
    occupation TEXT NOT NULL,
    social_status REAL NOT NULL,
    location_id TEXT NOT NULL,
    home_location_id TEXT NOT NULL,
    community_id TEXT,
    alive INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (experiment_id, agent_id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_agents_exp_loc ON agents(experiment_id, location_id);

CREATE TABLE IF NOT EXISTS agent_traits (
    experiment_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    openness REAL NOT NULL,
    conscientiousness REAL NOT NULL,
    extraversion REAL NOT NULL,
    agreeableness REAL NOT NULL,
    emotional_stability REAL NOT NULL,
    PRIMARY KEY (experiment_id, agent_id),
    FOREIGN KEY (experiment_id, agent_id) REFERENCES agents(experiment_id, agent_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_states (
    experiment_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    nutrition REAL NOT NULL,
    energy REAL NOT NULL,
    safety REAL NOT NULL,
    social_connection REAL NOT NULL,
    belonging REAL NOT NULL,
    achievement REAL NOT NULL,
    knowledge_acquisition REAL NOT NULL,
    resource_security REAL NOT NULL,
    last_action TEXT NOT NULL DEFAULT 'idle',
    last_reward REAL NOT NULL DEFAULT 0.0,
    cumulative_reward REAL NOT NULL DEFAULT 0.0,
    reputation REAL NOT NULL DEFAULT 0.5,
    PRIMARY KEY (experiment_id, agent_id),
    FOREIGN KEY (experiment_id, agent_id) REFERENCES agents(experiment_id, agent_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_resources (
    experiment_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    quantity REAL NOT NULL,
    PRIMARY KEY (experiment_id, agent_id, resource_type),
    FOREIGN KEY (experiment_id, agent_id) REFERENCES agents(experiment_id, agent_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_goals (
    experiment_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    goal_id TEXT NOT NULL,
    goal_type TEXT NOT NULL,
    target_value REAL NOT NULL,
    priority REAL NOT NULL,
    progress REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (experiment_id, agent_id, goal_id),
    FOREIGN KEY (experiment_id, agent_id) REFERENCES agents(experiment_id, agent_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_beliefs (
    experiment_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    belief_key TEXT NOT NULL,
    belief_value REAL NOT NULL,
    confidence REAL NOT NULL,
    updated_tick INTEGER NOT NULL,
    PRIMARY KEY (experiment_id, agent_id, belief_key),
    FOREIGN KEY (experiment_id, agent_id) REFERENCES agents(experiment_id, agent_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    memory_layer TEXT NOT NULL,
    tick INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    participants_json TEXT NOT NULL,
    context_json TEXT NOT NULL,
    outcome REAL NOT NULL,
    emotional_significance REAL NOT NULL,
    relevance_weight REAL NOT NULL,
    recall_count INTEGER NOT NULL DEFAULT 0,
    consolidated INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (experiment_id, agent_id) REFERENCES agents(experiment_id, agent_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_memories_agent ON agent_memories(experiment_id, agent_id, memory_layer, tick);

CREATE TABLE IF NOT EXISTS learning_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    tick INTEGER NOT NULL,
    state_key TEXT NOT NULL,
    action TEXT NOT NULL,
    q_value REAL NOT NULL,
    reward REAL NOT NULL,
    next_state_key TEXT NOT NULL,
    td_error REAL NOT NULL,
    source TEXT NOT NULL,
    FOREIGN KEY (experiment_id, agent_id) REFERENCES agents(experiment_id, agent_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_learning_agent_tick ON learning_records(experiment_id, agent_id, tick);

CREATE TABLE IF NOT EXISTS relationships (
    experiment_id TEXT NOT NULL,
    source_agent_id TEXT NOT NULL,
    target_agent_id TEXT NOT NULL,
    rel_type TEXT NOT NULL,
    weight REAL NOT NULL,
    trust REAL NOT NULL,
    interaction_count INTEGER NOT NULL,
    last_tick INTEGER NOT NULL,
    PRIMARY KEY (experiment_id, source_agent_id, target_agent_id, rel_type),
    FOREIGN KEY (experiment_id, source_agent_id) REFERENCES agents(experiment_id, agent_id) ON DELETE CASCADE,
    FOREIGN KEY (experiment_id, target_agent_id) REFERENCES agents(experiment_id, agent_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_rel_exp ON relationships(experiment_id, source_agent_id);

CREATE TABLE IF NOT EXISTS communities (
    experiment_id TEXT NOT NULL,
    community_id TEXT NOT NULL,
    name TEXT NOT NULL,
    founded_tick INTEGER NOT NULL,
    cohesion REAL NOT NULL,
    centroid_x REAL NOT NULL,
    centroid_y REAL NOT NULL,
    member_count INTEGER NOT NULL,
    PRIMARY KEY (experiment_id, community_id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS institutions (
    experiment_id TEXT NOT NULL,
    institution_id TEXT NOT NULL,
    name TEXT NOT NULL,
    inst_type TEXT NOT NULL,
    founder_id TEXT NOT NULL,
    founded_tick INTEGER NOT NULL,
    stability REAL NOT NULL,
    treasury_json TEXT NOT NULL,
    rules_json TEXT NOT NULL,
    compliance_rate REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (experiment_id, institution_id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS institution_members (
    experiment_id TEXT NOT NULL,
    institution_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    role TEXT NOT NULL,
    joined_tick INTEGER NOT NULL,
    contribution REAL NOT NULL,
    violations INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (experiment_id, institution_id, agent_id),
    FOREIGN KEY (experiment_id, institution_id) REFERENCES institutions(experiment_id, institution_id) ON DELETE CASCADE,
    FOREIGN KEY (experiment_id, agent_id) REFERENCES agents(experiment_id, agent_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cultural_traits (
    experiment_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    trait_name TEXT NOT NULL,
    trait_value TEXT NOT NULL,
    adoption_tick INTEGER NOT NULL,
    source_agent_id TEXT,
    PRIMARY KEY (experiment_id, agent_id, trait_name),
    FOREIGN KEY (experiment_id, agent_id) REFERENCES agents(experiment_id, agent_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL,
    tick INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    actor_id TEXT,
    target_id TEXT,
    location_id TEXT,
    payload_json TEXT NOT NULL,
    explanation_json TEXT,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_events_exp_tick ON events(experiment_id, tick);
CREATE INDEX IF NOT EXISTS idx_events_actor ON events(experiment_id, actor_id, tick);

CREATE TABLE IF NOT EXISTS metrics (
    experiment_id TEXT NOT NULL,
    tick INTEGER NOT NULL,
    population INTEGER NOT NULL,
    total_resources REAL NOT NULL,
    cooperation_index REAL NOT NULL,
    gini_coefficient REAL NOT NULL,
    mean_trust REAL NOT NULL,
    network_density REAL NOT NULL,
    community_count INTEGER NOT NULL,
    institution_count INTEGER NOT NULL,
    cultural_diversity REAL NOT NULL,
    mean_q_value REAL NOT NULL,
    mean_utility REAL NOT NULL,
    trade_volume REAL NOT NULL,
    collective_success_rate REAL NOT NULL,
    avg_need_satisfaction REAL NOT NULL,
    PRIMARY KEY (experiment_id, tick),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);
