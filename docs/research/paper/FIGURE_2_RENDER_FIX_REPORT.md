# Figure 2 Rendering Fix Report

**Project:** ManiGit: Transparent, Versioned Context Memory for Long-Running AI Agents  
**Target:** Figure 2: ManiGit System Architecture  
**File:** `docs/research/paper/figures/fig2_architecture.tex`  
**Date:** October 2026  

---

## 1. Root Cause Analysis

In `docs/research/paper/figures/fig2_architecture.tex`, the `databox` style applied to the `SQLite Archive` and `Versioned Commit DAG` components was defined as:
```latex
databox/.style={cylinder, shape border rotate=90, draw=purple!80, fill=purple!5, thick, minimum width=2.0cm, minimum height=1.1cm, align=center, font=\scriptsize}
```
In PGF/TikZ's `shapes.geometric` library, the `cylinder` shape with `shape border rotate=90` renders end-cap ellipses. In several pdfTeX rendering pipelines (including Overleaf's compiler), these rotated cylinder caps generate two large, malformed pink/purple elliptical/circular overlays directly over the component text. These visual artifacts obscured:
- `SQLite Archive (Immutable Msgs)`
- `Versioned Commit DAG (C_k)`

---

## 2. Figure Source Inspected

- **File Path:** [`docs/research/paper/figures/fig2_architecture.tex`](file:///c:/Users/Arshmeet/OneDrive/Desktop/Projects/ManiGit/docs/research/paper/figures/fig2_architecture.tex)
- **Associated Section:** Included in Section V (*ManiGit Architecture*) via `\input{figures/fig2_architecture.tex}` in [`docs/research/paper/sections/05_manigit_architecture.tex`](file:///c:/Users/Arshmeet/OneDrive/Desktop/Projects/ManiGit/docs/research/paper/sections/05_manigit_architecture.tex).
- **Environment:** Full-width `figure*` positioned at `[t]` with caption below.

---

## 3. Exact Erroneous Objects Removed

- Removed the TikZ `cylinder, shape border rotate=90` attribute from the `databox` style.
- Replaced with standard rounded database rectangle styling:
  ```latex
  databox/.style={rectangle, draw=purple!80, fill=purple!8, thick, rounded corners=3pt, minimum width=2.4cm, minimum height=0.9cm, align=center, font=\scriptsize}
  ```
- No architectural nodes, labels, or connections were removed. All 8 core components remain:
  1. `Incoming Message m_t`
  2. `Hybrid Intake (Rule Engine + LLM Judge)`
  3. `SQLite Archive (Immutable Msgs)`
  4. `Versioned Commit DAG (C_k)`
  5. `Contradiction Detector`
  6. `Memory Tiers (VERBATIM / SUMMARY)`
  7. `Context Compiler (Greedy Knapsack <= B)`
  8. `Compiled Context C_t subset M_t`

---

## 4. Figure Dimensions Before and After

- **Before:** Width bounded via `\resizebox{0.95\textwidth}{!}{...}`, height expanded by erratic vertical cylinder caps resulting in clipping and text obstruction.
- **After:** Preserved `\resizebox{0.95\textwidth}{!}{...}` with clean $2.4\text{ cm} \times 0.9\text{ cm}$ rectangular database containers. Zero text occlusion, zero oval overlays, and identical aspect ratio.

---

## 5. Other Figures Inspected

All other 8 figures in `docs/research/paper/figures/` were audited for accidental overlays or malformed shapes:
- **Fig. 1 (`fig1_history_timeline.tex`):** Verified clean rectangles and arrow connectors.
- **Fig. 3 (`fig3_memory_lifecycle.tex`):** Verified valid FSM state circles (`state/.style={circle, draw=blue!80...}`).
- **Fig. 4 (`fig4_context_compilation.tex`):** Verified clean knapsack boundary boxes.
- **Figs. 5–9 (PGFPlots):** Verified pure coordinate plots and bar charts without stray graphical overlays.

---

## 6. PDF Compilation & Static Paper Validation

- **Script:** `python scripts/validate_paper.py`
- **Result:** **PASSED (Zero Errors)**
  - All `.tex` files have balanced curly braces `{}`
  - Master and sub-input files intact
  - All citations, labels, and raw benchmark data 100% consistent

---

## 7. Codebase Regression Suite

- **Command:** `uv run pytest -q`
- **Result:** **176 passed in 4.39s (0 failed, 0 skipped)**

---

## 8. Confirmation of Zero Research/Code Modification

- Benchmark results (`exp_canonical_run_001.json`, `exp_ablation_run_001.json`): **UNCHANGED**
- Mathematical formulation: **UNCHANGED**
- ManiGit source code (`src/manigit/`): **UNCHANGED**
- Author/institution metadata: **UNCHANGED**
- Research claims & conclusions: **UNCHANGED**
