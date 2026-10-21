# Figure 2: ManiGit System Architecture Specification

## 1. Purpose
Serve as the primary system architecture diagram for ManiGit, communicating the end-to-end dataflow from incoming messages through hybrid classification, commit creation, contradiction detection, functional memory tiers, knapsack context compilation, and the resulting prompt passed to the model adapter.

## 2. Required Nodes
The figure must contain 8 functional blocks organized across two horizontal tracks (Execution Pipeline above, Storage/Commit DAG below):
- **Top Row (Runtime Execution Path):**
  - Node 1: `Incoming Message \ $m_t$` (Raw user or assistant turn)
  - Node 2: `Hybrid Intake \ Rule Engine + LLM Judge` (Deterministic pattern matching + confidence thresholding)
  - Node 3: `Contradiction \ Detector` (Semantic conflict detection against active branch facts)
  - Node 4: `Context Compiler \ Greedy Knapsack $\le B$` (Budget-constrained utility-density ranker)
- **Bottom Row (Persistent Substrate & State):**
  - Node 5: `SQLite Archive \ (Immutable Msgs)` (Append-only content-hashed raw store)
  - Node 6: `Versioned Commit \ DAG ($C_k$)` (SHA-256 parent-linked snapshot tree)
  - Node 7: `Memory Tiers \ VERBATIM / SUMMARY` (Functional active memory objects)
  - Node 8: `Compiled Context \ $C_t \subseteq \mathcal{M}_t$` (Budget-bounded prompt context for model)

## 3. Required Relationships (Directed Connectors)
- `Incoming Message (msg)` -> `Hybrid Intake (class)` (Message processing)
- `Incoming Message (msg)` -> `SQLite Archive (rawdb)` (Immutable append-only persistence)
- `Hybrid Intake (class)` -> `Versioned Commit DAG (dag)` [label: `Fact`] (New commit generation)
- `Hybrid Intake (class)` -> `Contradiction Detector (contra)` (Candidate conflict check)
- `Contradiction Detector (contra)` -> `Memory Tiers (tiers)` [label: `Archive Superseded`] (Lifecycle transition)
- `Versioned Commit DAG (dag)` -> `Memory Tiers (tiers)` (Active memory state provisioning)
- `Memory Tiers (tiers)` -> `Context Compiler (compiler)` (Candidate candidate pool $\mathcal{M}_t$)
- `Context Compiler (compiler)` -> `Compiled Context (prompt)` (Packed context $\sum L(m_i) \le B$)

## 4. Exact Labels
- Top Row:
  - `Incoming Message \ $m_t$`
  - `Hybrid Intake \ Rule Engine + LLM Judge`
  - `Contradiction \ Detector`
  - `Context Compiler \ Greedy Knapsack $\le B$`
- Bottom Row:
  - `SQLite Archive \ (Immutable Msgs)`
  - `Versioned Commit \ DAG ($C_k$)`
  - `Memory Tiers \ VERBATIM / SUMMARY`
  - `Compiled Context \ $C_t \subseteq \mathcal{M}_t$`
- Arrow Labels:
  - `Fact`
  - `Archive Superseded`

## 5. Prohibited Elements
- NO decorative cylinders, circles, or ellipses.
- NO floating arrows or disconnected endpoints.
- NO arrows crossing through node boxes or text labels.
- NO ungrounded databases or fictional cloud microservices.
- NO pink/red overlay shapes.

## 6. Layout & Geometry
- Two-tier rectangular card layout with clean orthogonal and straight connectors.
- Double-column IEEE width: `0.95\textwidth` (approx. 17.5 cm).
- Height: approx. 4.2 cm to 4.8 cm.
- Equal horizontal spacing between pipeline stages.

## 7. Typography
- IEEE standard typeface (Computer Modern / Latin Modern / Times).
- Node text: 8 pt to 9 pt (`\scriptsize`).
- Math mode formatting: $m_t$, $C_k$, $B$, $C_t \subseteq \mathcal{M}_t$.

## 8. Colors (Grayscale-Friendly)
- Processing pipeline boxes: Light steel blue (`blue!5` fill, `blue!80` border, 0.8pt line).
- Persistent storage boxes: Light purple/slate (`purple!8` fill, `purple!80` border, 0.8pt line).
- Connectors: Neutral dark charcoal (`gray!90`, thick stealth arrowheads).

## 9. Output Dimensions & Target Format
- Dimensions: 175 mm x 45 mm.
- Primary format: TikZ vector source (`fig2_architecture.tex`).
- Export format: Vector PDF / SVG.
