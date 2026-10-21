# Figure 1: Historical Evolution Timeline Specification

## 1. Purpose
Illustrate the five-decade evolutionary trajectory of AI memory architectures from classical symbolic production rules and formal belief revision to differentiable neural memory, retrieval-augmented generation (RAG), operating-system-inspired paging, and transparent versioned context memory (ManiGit).

## 2. Required Nodes
The figure must contain 10 chronological stages across three horizontal tiers:
- **Tier 1 (Foundations & Neural Memory):**
  - Node 1: `1972: Newell & Simon — Working Memory` (Production systems, working memory buffer)
  - Node 2: `1985: AGM Logic — Belief Revision` (Alchourrón, Gärdenfors, Makinson postulates)
  - Node 3: `2014: NTM / MemNN — Neural Memory` (Neural Turing Machines, Memory Networks)
  - Node 4: `2017: Transformer — Self-Attention` (Vaswani et al., multi-head attention)
- **Tier 2 (Retrieval & Modern Agent Memory):**
  - Node 5: `2020: RAG — Retrieval Augmentation` (Lewis et al., REALM, vector retrieval)
  - Node 6: `2023: Generative Agents — Memory Streams` (Park et al., importance/recency streams)
  - Node 7: `2023: MemGPT — Paged OS Memory` (Packer et al., LLM OS paging via tool calls)
  - Node 8: `2024: Mem0 / HippoRAG — Graph & Fact Stores` (Multi-scope, hippocampal PageRank)
- **Tier 3 (Git Metaphors & Proposed Work):**
  - Node 9: `2025: GCC / GitOfThoughts — Git Reasoners` (Explicit agent-tool Git commits)
  - Node 10: `2026: ManiGit (This Work) — Transparent Versioned Context Memory` (Automated commit DAG, knapsack compiler)

## 3. Required Relationships (Directed Arrows)
- `s1 (1972)` -> `s2 (1985)`
- `s2 (1985)` -> `s3 (2014)`
- `s3 (2014)` -> `s4 (2017)`
- `s4 (2017)` -> `s8 (2024)`
- `s5 (2020)` -> `s6 (2023)`
- `s6 (2023)` -> `s7 (2023)`
- `s7 (2023)` -> `s8 (2024)`
- `s8 (2024)` -> `s9 (2025)`
- `s9 (2025)` -> `s10 (2026)`
- `s5 (2020)` -> `s10 (2026)` (Evolution from atemporal RAG to versioned context memory)

## 4. Exact Labels
All labels must exactly match cited literature:
- `1972: Newell & Simon \ Working Memory`
- `1985: AGM Logic \ Belief Revision`
- `2014: NTM / MemNN \ Neural Memory`
- `2017: Transformer \ Self-Attention`
- `2020: RAG \ Retrieval Augmentation`
- `2023: Generative Agents \ Memory Streams`
- `2023: MemGPT \ Paged OS Memory`
- `2024: Mem0 / HippoRAG \ Graph & Fact Stores`
- `2025: GCC / GitOfThoughts \ Git Reasoners`
- `2026: ManiGit (This Work) \ Transparent Versioned Context Memory`

## 5. Prohibited Elements
- No floating pointers or arrows terminating in whitespace.
- No labels sitting directly on top of arrow shafts.
- No crossing arrows.
- No decorative 3D effects, shadows, or glossy gradients.
- No non-cited systems or fictitious years.

## 6. Layout & Geometry
- Top-to-bottom three-tier flow with left-to-right progression within tiers.
- Grid-aligned rectangular cards with uniform corner radius (2pt–3pt).
- Double-column IEEE width: `0.95\textwidth` (approx. 17.5 cm).
- Height: approx. 4.5 cm to 5.0 cm.

## 7. Typography
- IEEE standard font family (Times / LaTeX default serif or sans).
- Node text: 8 pt to 9 pt (`\scriptsize` in LaTeX).
- Node titles: Bold.

## 8. Colors (Grayscale-Friendly)
- Historical literature nodes (1–8): Subtle cool blue/gray (`blue!8` fill, `blue!70` border).
- Git reasoners node (9): Muted amber/orange (`orange!15` fill, `orange!80` border).
- ManiGit node (10): Distinct highlighted green (`green!15` fill, `green!80` border).
- Arrows: Dark gray / neutral slate (`gray!80`, stealth arrowheads).

## 9. Output Dimensions & Target Format
- Dimensions: 175 mm x 50 mm.
- Primary format: TikZ/PGF vector source (`fig1_history_timeline.tex`).
- Export format: Vector PDF / SVG.
