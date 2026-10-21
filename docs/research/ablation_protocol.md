# ManiGit Controlled Ablation Protocol

## 1. Research Question
**"Which components of ManiGit contribute to memory quality, historical correctness, contradiction handling, provenance, and budget-aware context selection?"**

## 2. Formal Research Hypotheses
- **H1 (Budget-Constrained Robustness)**: ManiGit Full provides superior factual recall and answer correctness compared to non-versioned memory baselines under constrained token budgets ($B \le 256$).
- **H2 (Historical Reconstruction Integrity)**: ManiGit's immutable DAG structure and commit snapshots enable 100% reliable historical reconstruction of previously valid facts superseded in active state.
- **H3 (Contradiction Adjudication Contribution)**: Contradiction and supersession detection materially improves current-state correctness and contradiction accuracy on scenarios with conflicting assertions.
- **H4 (Confidence-Aware Classification Robustness)**: Confidence-aware escalation prevents silent information loss for ambiguous, tentative, or low-certainty statements.
- **H5 (Tier-Aware Selection Efficiency)**: Tier-aware boosting (prioritizing VERBATIM constraints over verbose SUMMARY items) significantly improves the utility and compactness of selected context under tight token budgets ($B=128$).

## 3. Experimental Variables
### Independent Variables
1. **Context Management Strategy / Variant** (8 levels):
   - Reference Baseline A: Full History (unbounded dialogue concatenation)
   - Reference Baseline B: Sliding Window ($N=10$ turns)
   - Reference Baseline C: Running Summary (condensed dialogue points)
   - Reference Baseline D: RAG-Style Retrieval (lexical turn-level Jaccard matching)
   - Reference Condition E: ManiGit Full (versioned memory + rules/judge + tiers + contradiction detection)
   - Ablation Variant F: ManiGit (no_contradiction)
   - Ablation Variant G: ManiGit (no_confidence)
   - Ablation Variant H: ManiGit (no_tier)
2. **Context Budget** $B$ (5 levels): $B \in \{128, 256, 512, 1024, 2048\}$ tokens.
3. **Scenario Category / Dialogue Flow** (11 scenarios, 22 queries).

### Dependent Variables
1. **Fact Recall** (Boolean $\in \{0, 1\}$): Whether the expected fact or acceptable alternative is present in compiled context.
2. **Answer Correctness** (Boolean $\in \{0, 1\}$): Whether the generated answer matches the expected ground-truth fact.
3. **Historical Recovery Rate** (Boolean $\in \{0, 1\}$): Whether an earlier version of a fact was retrieved when historical state was queried.
4. **Contradiction Accuracy** (Boolean $\in \{0, 1\}$): Whether the system correctly identifies current vs. superseded facts.
5. **Context Token Consumption** (Integer $\ge 0$): Exact tokens occupied by compiled context.
6. **Total Token Consumption** (Integer $\ge 0$): Context tokens + prompt tokens + output tokens.
7. **Budget Utilization** (Float $\in [0.0, 1.0]$): Context tokens divided by budget $B$.
8. **Retrieval Precision & Recall** (Floats $\in [0.0, 1.0]$): Dialogue turn overlap against relevant turn indices.
9. **Latency** (Milliseconds): Context compilation latency and generation latency.

### Controlled Variables
- Identical raw conversation transcripts and turn sequences.
- Identical query phrasing and query presentation order.
- Identical token budgets $B$ across all methods.
- Deterministic pseudo-random seed (42).
- Uniform evaluation grading rules across all methods.
- Offline deterministic mock model adapter calibrated identically for all conditions.
- Strict isolation of memory databases (in-memory SQLite per evaluation run).

## 4. Ablation Semantic Definitions
Each ablation differs from ManiGit Full by exactly **ONE** isolated mechanism:

### F. ManiGit (no_contradiction)
- **Mechanism Neutralized**: Contradiction and supersession detection.
- **Operational Implementation**: Evaluated using `DisabledContradictionDetector`, where `.detect()` unconditionally returns `has_contradiction=False`.
- **System Behavior**: When a later fact contradicts an earlier active memory (e.g., PostgreSQL replaced by MongoDB), the earlier memory is NOT tombstoned or superseded. Both facts remain simultaneously active in the commit state. When queried for current state, unadjudicated conflicting facts cause failure or ambiguity.
- **Guarantees Preserved**: Immutable commits, SQLite schema, rules, confidence, and context ranking scoring remain untouched.

### G. ManiGit (no_confidence)
- **Mechanism Neutralized**: Confidence-aware classification threshold and confidence ranking weight.
- **Operational Implementation**: Evaluated using `NoConfidenceMemoryClassifier`, where `ARCHIVE_CONFIDENCE_THRESHOLD = 0.0` (disabling escalation of low-confidence items to VERBATIM), and `ScoringWeights.confidence_weight = 0.0`.
- **System Behavior**: Confidence scores remain stored in memory metadata, but decisions ignore confidence. Tentative statements recommended as ARCHIVED (0.55 confidence) are archived immediately without conservative escalation, resulting in fact loss for ambiguous queries.
- **Guarantees Preserved**: Contradiction detection, rules, tiers, and token budgets remain untouched.

### H. ManiGit (no_tier)
- **Mechanism Neutralized**: Tier-specific preference and boosting during context selection.
- **Operational Implementation**: Evaluated using `ScoringWeights(verbatim_boost=0.0, summary_boost=0.0)`.
- **System Behavior**: Memories retain their assigned tiers (VERBATIM / SUMMARY) in storage, but context compilation ranking applies zero tier-specific bonus. When concise verbatim constraints compete with verbose summaries of equal relevance, recency ordering dominates, causing verbose summaries to consume the budget and exclude verbatim constraints under tight budgets ($B=128$).
- **Guarantees Preserved**: Storage tiers, rules, judge, contradiction detection, and confidence scoring remain untouched.

## 5. Fairness Controls
- **Zero Hidden Information**: No baseline or ablation receives access to metadata, hints, or messages unavailable to other methods.
- **No Hardcoded Answers**: Model adapters evaluate queries solely based on the compiled context provided.
- **Evaluation-Layer Adapters**: Production code is never artificially degraded to favor ManiGit. All ablations operate via clean evaluation adapters (`DisabledContradictionDetector`, `NoConfidenceMemoryClassifier`, evaluation `ScoringWeights`).

## 6. Scenario Matrix
The suite contains 11 benchmark scenarios spanning 22 queries:
1. `stable_facts`: Evaluates retention of static system facts across conversational noise.
2. `superseding_facts`: Evaluates contradiction handling (PostgreSQL $\to$ MongoDB) and historical reconstruction.
3. `exact_constraints`: Evaluates retention of numeric and boundary constraints (500 ms timeout, 16 workers).
4. `decisions`: Evaluates retention of architecture decisions (JWT auth, event sourcing billing).
5. `technical_facts`: Evaluates exact paths, identifiers, and error codes (`/etc/manigit/runtime.conf`, `ERR_SOCKET_TIMEOUT_902`).
6. `distractors`: Evaluates retention when critical facts are submerged in 25 conversational distractor turns.
7. `duplicates`: Evaluates deduplication and noise suppression across repeated assertions.
8. `long_50`: Evaluates scaling over 50 dialogue turns.
9. `long_100`: Evaluates scaling over 100 dialogue turns.
10. `ambiguous_confidence`: Evaluates conservative escalation of low-confidence tentative statements.
11. `tier_competition`: Evaluates prioritization of concise verbatim constraints over verbose summaries under tight budgets ($B=128$).

## 7. Statistical Methodology
- **Wilson Score Intervals**: Computed at 95% confidence ($\alpha = 0.05$, $z = 1.95996$) for all binomial metrics. Provides accurate asymmetric coverage even for boundary conditions ($p=0.0$ or $p=1.0$).
- **Paired Comparisons**: When evaluating ablation degradation relative to ManiGit Full, trials are paired strictly on `(scenario_id, query_id, budget)`, ensuring zero cross-scenario variance confounding.
- **Continuous Metrics**: Reported with sample mean, standard deviation, median, min, and max.
- **Zero Fabrication**: All reported tables, metrics, and figure files are generated directly from the 880 raw trial records in `exp_ablation_run_001.json`.
