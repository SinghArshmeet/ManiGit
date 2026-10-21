# Figure 3: Four-Tier Memory Lifecycle Specification

## 1. Purpose
Illustrate the finite state machine governing memory lifecycle transitions in ManiGit. Shows how incoming dialogue turns transition into active memory tiers (`VERBATIM`, `SUMMARY`), and how evolving dialogue causes automated transitions to terminal/historical states (`ARCHIVED`, `TOMBSTONE`).

## 2. Required Nodes (States)
- **Originating Input:**
  - `Raw \ Turn` (Incoming conversational turn)
- **Active Memory Tiers (Context Compiler Candidates):**
  - `VERBATIM \ Exact Fact` (High-confidence constraints, decisions, technical specs)
  - `SUMMARY \ Overview` (Synthesized conversational context and broad goals)
- **Historical / Inactive Tiers (Excluded from Active Compilation, Retained for DAG History):**
  - `ARCHIVED \ Superseded` (Facts superseded by a newer contradictory statement)
  - `TOMBSTONE \ Retracted` (Explicitly retracted or refuted premises)

## 3. Required State Transitions (Directed Arrows)
- `Raw Turn` -> `VERBATIM` [label: `Rule / High Conf ($c \ge 0.85$)`]
- `Raw Turn` -> `SUMMARY` [label: `Discussion ($c \ge 0.70$)`]
- `VERBATIM` -> `ARCHIVED` [label: `Contradicted`]
- `SUMMARY` -> `TOMBSTONE` [label: `Invalidated`]
- `VERBATIM` -> `TOMBSTONE` [label: `Explicit Refute`]

## 4. Exact Labels
- States:
  - `Raw \ Turn`
  - `\textbf{VERBATIM} \ Exact Fact`
  - `\textbf{SUMMARY} \ Overview`
  - `\textbf{ARCHIVED} \ Superseded`
  - `\textbf{TOMBSTONE} \ Retracted`
- Transition Annotations:
  - `Rule / High Conf`
  - `Discussion`
  - `Contradicted`
  - `Invalidated`
  - `Explicit Refute`

## 5. Prohibited Elements
- No circular loops or ambiguous back-transitions (active memories cannot self-resurrect without a new commit).
- No floating pointers.
- No deletion transitions (memory is never dropped or deleted, only transitioned).

## 6. Layout & Geometry
- Single-column IEEE format: `0.92\columnwidth` (approx. 8.2 cm).
- Left-to-right progression from Raw Turn to active tiers, then to historical tiers.
- Node shapes: Uniform circles or rounded capsules (`minimum size=1.4cm`).

## 7. Typography
- IEEE standard font family.
- State names: Bold, 8 pt (`\textbf{VERBATIM}`).
- Subtitles: 7 pt (`\scriptsize` / `\tiny`).
- Transition labels: 6.5 pt (`\tiny`).

## 8. Colors (Grayscale-Friendly)
- Active states: Soft blue fill (`blue!10`, `blue!80` border).
- Transition arrows: Slate gray (`gray!90`, thick stealth arrowheads).
- High-contrast text labels.

## 9. Output Dimensions & Target Format
- Dimensions: 85 mm x 45 mm.
- Primary format: TikZ vector source (`fig3_memory_lifecycle.tex`).
- Export format: Vector PDF / SVG.
