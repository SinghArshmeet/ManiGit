# Overleaf Import & IEEE Compilation Guide

**Project:** ManiGit — Transparent, Versioned Context Memory for Long-Running AI Agents  
**Paper Directory:** `docs/research/paper/`  
**Master Document:** `PAPER.tex`  
**Class File:** `IEEEtran.cls` (v1.8b bundled)  
**BibTeX Style:** `IEEEtran.bst` (v1.14 bundled)  
**Bibliography:** `references.bib` (34 verified references)  
**Layout:** Standard IEEE Conference Two-Column Format  

---

## 1. Quick Start: Importing into Overleaf

To compile this research paper in Overleaf:

1. **Zip the Paper Directory:**
   Compress the entire contents of `docs/research/paper/` into a single `.zip` file:
   - `PAPER.tex` (Main entry point)
   - `IEEEtran.cls` (Official IEEE document class)
   - `IEEEtran.bst` (Official IEEE BibTeX style)
   - `references.bib` (Master BibTeX database)
   - `sections/` (All 14 modular section `.tex` files)
   - `figures/` (All native TikZ and PGFPlots `.tex` files)
   - `tables/` (All IEEE-formatted booktabs `.tex` files)
2. **Create New Project in Overleaf:**
   - Log into your Overleaf account (https://www.overleaf.com).
   - Click **New Project** $\to$ **Upload Project**.
   - Select the `.zip` file created in Step 1.
3. **Verify Project Settings:**
   - Ensure `PAPER.tex` is set as the **Main document** (via Menu in the top left or file tree).
   - Set Compiler to **pdfLaTeX** (standard and recommended for IEEEtran).
   - Set TeX Live version to **2023**, **2024**, or later.
4. **Compile:**
   - Click **Recompile**.
   - Overleaf will compile the document and render the final publication-ready IEEE two-column PDF.

---

## 2. Directory Structure

The paper repository is organized in a clean, self-contained modular structure:

```text
docs/research/paper/
├── PAPER.tex                  <- Master IEEEtran document importing all sections
├── IEEEtran.cls               <- Official IEEE document class (v1.8b)
├── IEEEtran.bst               <- Official IEEE BibTeX style file (v1.14)
├── references.bib             <- Master BibTeX file (34 verified entries)
├── README_OVERLEAF.md         <- Overleaf setup & compilation guide
├── IEEE_FORMAT_AUDIT.md       <- Itemized IEEEtran compliance audit (PASS/FAIL)
├── FINAL_CONTENT_INTEGRITY_AUDIT.md <- Publication integrity & bibliography audit
├── PHASE_10_IEEE_FORMAT_REPORT.md <- Phase 10 completion report
├── artifact_traceability.md   <- End-to-end data provenance from raw JSON to LaTeX
│
├── sections/                  <- Modular section files
│   ├── 01_introduction.tex
│   ├── 02_background.tex
│   ├── 03_history_and_related_work.tex
│   ├── 04_research_gap.tex
│   ├── 05_manigit_architecture.tex
│   ├── 06_mathematical_formulation.tex
│   ├── 07_methodology.tex
│   ├── 08_results.tex
│   ├── 09_ablation.tex
│   ├── 10_discussion.tex
│   ├── 11_threats_validity.tex
│   ├── 12_limitations.tex
│   ├── 13_future_work.tex
│   └── 14_conclusion.tex
│
├── tables/                    <- IEEE two-column optimized booktabs tables
│   ├── table1_overall_comparison.tex  (table*, full-width comparison)
│   ├── table2_ablation_degradation.tex (table, column-width paired degradation)
│   ├── table3_budget_breakdown.tex    (table*, full-width budget breakdown)
│   └── table4_mechanism_scenarios.tex (table*, full-width mechanism scenarios)
│
└── figures/                   <- IEEE two-column optimized vector figures
    ├── fig1_history_timeline.tex      (figure*, full-width 5-decade timeline)
    ├── fig2_architecture.tex          (figure*, full-width ManiGit architecture)
    ├── fig3_memory_lifecycle.tex      (figure, column-width 4-tier state machine)
    ├── fig4_context_compilation.tex    (figure, column-width knapsack selection)
    ├── fig5_budget_performance.tex    (figure, column-width PGFPlots chart)
    ├── fig6_historical_recovery.tex    (figure, column-width PGFPlots chart)
    ├── fig7_contradiction_handling.tex (figure, column-width PGFPlots chart)
    ├── fig8_ablation_degradation.tex   (figure, column-width PGFPlots chart)
    └── fig9_efficiency_tradeoff.tex   (figure, column-width PGFPlots Pareto)
```

---

## 3. Required LaTeX Packages

All required packages are standard and included by default in Overleaf and all modern TeX Live / MacTeX / MikTeX installations:

| Package | Purpose in IEEEtran Layout |
| :--- | :--- |
| `IEEEtran.cls` | Official IEEE conference document class |
| `cite` | Automatic citation sorting and range compression (e.g., `[1]--[3]`) |
| `amsmath, amssymb, amsfonts` | Mathematical equations, knapsack optimization notation |
| `booktabs, multirow, array` | Publication-grade academic tables without vertical lines |
| `graphicx, xcolor` | Figure scaling and curated academic color palette |
| `tikz` | Native vector diagrams (timeline, architecture, state machine, knapsack) |
| `pgfplots` | Native vector plotting from empirical coordinate data (`compat=1.18`) |
| `microtype` | Sub-pixel typographical justification |
| `url, hyperref` | Hyperlinks configured for clean monochrome IEEE appearance |

*Note:* In accordance with IEEE publication requirements, the `geometry` package is intentionally omitted, preserving the official IEEEtran margin and column geometry.

---

## 4. Two-Column Layout Sizing Guidelines

In IEEE conference format, page layout is divided into two 3.5-inch columns with a 0.2-inch gutter. To guarantee zero horizontal overflow (`overfull \hbox`):
- **Full-Width Floats (`table*`, `figure*`):** Used for wide structures requiring two columns (Timeline, Architecture, multi-metric comparison tables). Tables are sized using `\resizebox{\textwidth}{!}{...}`.
- **Single-Column Floats (`table`, `figure`):** Used for compact structures. Sized to fit within a single column using `\resizebox{\columnwidth}{!}{...}`.
- **PGFPlots Charts (Figs. 5–9):** Width is configured to `0.98\columnwidth` with compact fonts (`font=\small` and `tick label style={font=\footnotesize}`), ensuring axis labels and legends fit cleanly within a single column.

---

## 5. Local Command-Line Compilation Workflow

If compiling locally with a command-line TeX distribution:

```bash
pdflatex PAPER
bibtex PAPER
pdflatex PAPER
pdflatex PAPER
```

This sequence resolves:
1. Pass 1: Identifies citations (`\cite{}`), labels (`\label{}`), and inputs.
2. Pass 2 (`bibtex`): Generates bibliography entries according to `IEEEtran.bst`.
3. Pass 3: Injects numbered bracketed citations (`[1]`, `[2]`).
4. Pass 4: Resolves cross-references (`Fig.~\ref{...}`, `Table~\ref{...}`, `\eqref{...}`).

---

## 6. Troubleshooting Common Overleaf Issues

1. **Undefined References or Citations:**
   - Overleaf automatically runs BibTeX. If `[?]` appears, click the small triangle next to **Recompile**, select **Clear cached files**, and recompile.
2. **PGFPlots Compatibility Warning:**
   - `PAPER.tex` specifies `\pgfplotsset{compat=1.18}`. If compiling on an older TeX Live (< 2021), adjust to `\pgfplotsset{compat=default}`.
3. **TikZ Library Warnings:**
   - The document utilizes standard TikZ libraries: `shapes.geometric`, `arrows`, `positioning`, `fit`, `calc`. All are standard in TeX Live.
4. **Table / Figure Placement:**
   - In two-column documents, `table*` and `figure*` floats can only be placed at the top of a page (`[t]`). This is standard IEEE behavior.
