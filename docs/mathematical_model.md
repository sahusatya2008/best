# EIDOLON Mathematical & Algorithmic Specification

## 1. Utility-Based Decision Engine
For each feasible action $a \in \mathcal{A}$ in state $s$, the utility function computes:

$$U(s, a) = 0.34\,N(a) + 0.22\,E[R(s, a)] + 0.14\,P(a) + 0.14\,S(a) + 0.12\,A(a) + 0.10\,M(a) + 0.12\,G(a) + 0.06\,U_{\text{unc}}(a) - 0.18\,C(a) - 0.16\,\rho(a)$$

Where:
- $N(a)$: Need satisfaction alignment with the agent's 8 normalized needs $\in [0, 1]$.
- $E[R(s, a)] = 0.55\,Q(s, a) + 0.45\,\bar{r}_{\text{proc}}(a)$: Blended tabular Q-value and procedural expectation.
- $P(a)$: Linear combination of Big Five traits (`openness`, `conscientiousness`, `extraversion`, `agreeableness`, `emotional_stability`) and cultural trait alignment.
- $S(a)$: Social trust, cooperation synergy, and institutional norm bonuses/penalties.
- $A(a)$: Local resource or partner availability.
- $M(a)$: Similarity-weighted outcome of top-$k$ retrieved episodic memories.
- $G(a)$: Active goal priority alignment.
- $U_{\text{unc}}(a) = \frac{1}{1 + 0.25\,n_a}(0.35 + 0.65\,\text{openness})$: Novelty exploration bonus.
- $C(a)$: Metabolic energy and input cost.
- $\rho(a)$: Local hazard, social retaliation, and failure penalty.

Action selection uses $\epsilon$-guided stochastic exploration with probability $\epsilon_{\text{eff}} = \epsilon \cdot (0.6 + 0.6\,\text{openness})$, otherwise Boltzmann softmax over top-3 feasible actions with temperature $\tau = 0.08 + 0.06(1 - \text{conscientiousness})$ using `SeededRNG`.

## 2. Tabular Q-Learning & Failure Adaptation
$$Q(s, a) \leftarrow Q(s, a) + \alpha \left[ r + \gamma \max_{a'} Q(s', a') - Q(s, a) \right]$$

For negative immediate outcomes occurring within the same discrete state ($r < 0$ and $s' = s$), bootstrapping from sibling actions is suppressed ($y = r$) and the action failure counter increments, increasing $\rho(a)$ in future evaluations.

## 3. Local Memory Similarity Retrieval
Each episodic memory stores a 5D feature vector $\mathbf{v}_m = [\text{urgency}, \text{scarcity}, \text{social\_density}, \text{safety}, \text{outcome}]^\top$. Retrieval ranks memories by:

$$\text{sim}(q, m) = 0.45 \max\!\left(0, \frac{\mathbf{v}_q \cdot \mathbf{v}_m}{\|\mathbf{v}_q\| \|\mathbf{v}_m\|}\right) + 0.18\,\mathbb{I}[\text{loc}_q = \text{loc}_m] + \frac{0.20}{1 + 0.015\,\Delta t} + 0.20\,e_m + 0.15\,w_m$$

## 4. Asymmetric Trust Dynamics
- Positive interaction ($\text{cooperate}$, $\text{trade}$, $\text{communicate}$): $T_{ij} \leftarrow T_{ij} + \eta_+(1 - T_{ij})$ where $\eta_+ \in \{0.05, 0.09, 0.14\}$.
- Competitive/violating interaction ($\text{compete}$, $\text{violate}$): $T_{ij} \leftarrow T_{ij} - \eta_- T_{ij}$ where $\eta_- \in \{0.22, 0.32\}$ (faster trust erosion than accumulation).

## 5. Scarcity Economics & Gini Inequality
Exchange prices update smoothly from aggregate supply vs. population baseline demand:
$$p_r^{(t)} = 0.75\,p_r^{(t-1)} + 0.25\,p_r^{\text{base}} \cdot \text{clip}\!\left(\frac{N \cdot d_r}{\max(1, \sum_i q_{i,r})}, 0.4, 4.0\right)$$
Wealth inequality is computed directly over agent inventories via the exact Gini formula:
$$G = \frac{\sum_{i=1}^{N} (2i - N - 1) w_{(i)}}{N \sum_{i=1}^{N} w_i}$$

## 6. Simplified Modeling Assumptions
1. Spatial movement occurs along a connected 2D graph rather than continuous collision physics.
2. Seasonal factors modulate regional regeneration rates uniformly per resource class.
3. State-space discretization buckets continuous needs/scarcity into compact keys for memory efficiency on 8 GB RAM hardware.
