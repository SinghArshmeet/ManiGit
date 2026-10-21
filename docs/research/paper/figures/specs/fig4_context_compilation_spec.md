# Figure 4: Mathematical Context Compilation Specification

## 1. Purpose
Illustrate the bounded knapsack selection process during context compilation. Shows how active candidate memory objects of varying token lengths and utility densities are evaluated under a hard token budget $B$, packing the highest density items into the compiled context window $C_t$ while cleanly excluding oversized or lower-utility candidates without exceeding $B$.

## 2. Required Elements
- **Candidate Memory Pool ($\mathcal{M}_t$):**
  - Item 1: `$m_1$: Summary (65 tok)` (Lower density / larger item, unselected under $B=128$)
  - Item 2: `$m_2$: Verb (28 tok)` (High density verbatim item, selected)
  - Item 3: `$m_3$: Verb (34 tok)` (High density verbatim item, selected)
  - Item 4: `$m_4$: Note (80 tok)` (Oversized item, unselected)
- **Compiled Context Window Container ($C_t$):**
  - Bounded box with dashed boundary representing the token limit $B = 128$.
  - Exact contents: $m_2$ (28 tok) + $m_3$ (34 tok) = 62 tokens $\le 128$.
- **Selection Connectors:**
  - Directed arrows from $m_2$ and $m_3$ into the compiled context container.

## 3. Required Relationships
- Candidates $m_2$ and $m_3$ are highlighted as active/selected and point directly into the container $C_t$.
- Candidates $m_1$ and $m_4$ remain in the candidate row outside the compiled window.

## 4. Exact Labels
- Candidate items:
  - `$m_1$: Summary (65 tok)`
  - `$m_2$: Verb (28 tok)`
  - `$m_3$: Verb (34 tok)`
  - `$m_4$: Note (80 tok)`
- Container label:
  - `\textbf{Compiled Context Window $C_t$} (Limit $B=128$ tokens)`
  - `Selected: $m_2$ (28 tok) + $m_3$ (34 tok) = 62 tokens $\le 128$`

## 5. Prohibited Elements
- Do NOT duplicate large mathematical formulas already given in Section VI equations.
- Do NOT show partial or split tokens (knapsack items are 0-1 atomic memory units).
- No floating pointers or confusing bidirectional arrows.

## 6. Layout & Geometry
- Single-column IEEE format: `0.98\columnwidth` (approx. 8.5 cm).
- Top: Horizontal row of candidate items.
- Bottom: Dashed container box enclosing selected context.
- Height: approx. 3.2 cm to 3.8 cm.

## 7. Typography
- IEEE standard font family.
- Labels: 7.5 pt to 8.5 pt (`\scriptsize`).
- Math mode formatting: $m_i$, $C_t$, $B=128$.

## 8. Colors (Grayscale-Friendly)
- Unselected candidates: Muted neutral gray (`gray!10` fill, `gray!70` border).
- Selected candidates: Distinct light green (`green!15` fill, `green!80` border).
- Context container: High-contrast dashed black boundary (`draw=black, dashed, thick`).
- Ingestion arrows: Blue directional indicators (`blue!80`).

## 9. Output Dimensions & Target Format
- Dimensions: 85 mm x 35 mm.
- Primary format: TikZ vector source (`fig4_context_compilation.tex`).
- Export format: Vector PDF / SVG.
