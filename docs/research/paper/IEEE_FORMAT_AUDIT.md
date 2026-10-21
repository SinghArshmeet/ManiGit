# IEEE Format Audit: ManiGit Research Paper

**Document:** `docs/research/paper/PAPER.tex`  
**Class:** `IEEEtran.cls` (v1.8b, `\documentclass[conference]{IEEEtran}`)  
**Bibliography Style:** `IEEEtran.bst` (v1.14)  
**Target Venue Mode:** IEEE Conference Two-Column Format  
**Audit Date:** October 2026  

---

## 1. Compliance Checklist

| Item | Requirement | Status | Detailed Audit Evidence / Verification |
| :--- | :--- | :---: | :--- |
| 1 | **IEEEtran document class** | **PASS** | `\documentclass[conference]{IEEEtran}` set in `PAPER.tex`. Official `IEEEtran.cls` (v1.8b, CTAN release) bundled in paper directory. |
| 2 | **Two-column layout** | **PASS** | Standard IEEE conference two-column layout enforced by document class. Margin/column geometry preserved without overriding `geometry` package. |
| 3 | **Title formatting** | **PASS** | `\title{ManiGit: Transparent, Versioned Context Memory\\for Long-Running AI Agents}` uses standard IEEE conference title styling with clean line breaking and no marketing language. |
| 4 | **Author formatting** | **PASS** | Formatted using `\IEEEauthorblockN{Arshmeet Singh}` and `\IEEEauthorblockA{\textit{Chandigarh University} \\ Mohali, Punjab, India}`. Valid single-author IEEE block without fabricated affiliations, lab names, or emails. |
| 5 | **Abstract** | **PASS** | Structured academic abstract enclosed in `\begin{abstract} ... \end{abstract}` covering problem, research gap, approach, empirical methodology, findings, and contributions. No exaggerated or unsubstantiated claims. |
| 6 | **IEEE keywords** | **PASS** | Enclosed in `\begin{IEEEkeywords} ... \end{IEEEkeywords}`. Contains 7 curated IEEE terms: Large Language Models, LLM Agents, Agent Memory, Persistent Memory, Context Management, Versioned Memory, Token-Budget Optimization. |
| 7 | **Section hierarchy** | **PASS** | Numbered sections follow IEEE convention: 14 primary sections (`\section{...}`) and hierarchical subsections (`\subsection{...}`). No unnumbered ad-hoc headers. |
| 8 | **Equation formatting** | **PASS** | Bounded knapsack optimization, utility formulation, and greedy selection equations are formalized with standard LaTeX math packages (`amsmath`, `amssymb`), labeled via `\label{eq:...}`, and referenced via `\eqref{...}`. Variables ($M, C_t, m_i, U, L, B, q_t$) are rigorously defined. |
| 9 | **Figure formatting** | **PASS** | All 9 figures (Figs. 1–9) labeled via `\label{fig:...}`, referenced in-text as `Fig.~\ref{fig:...}`, equipped with descriptive captions above/below as appropriate. Sized with `figure*` (`\textwidth`) for wide diagrams (Figs. 1–2) and single-column `figure` (`\columnwidth`) for state machine, knapsack, and PGFPlots (Figs. 3–9). |
| 10 | **Table formatting** | **PASS** | All 4 tables formatted with `booktabs` (`\toprule`, `\midrule`, `\bottomrule`), captions on top, labeled via `\label{tab:...}`, and referenced in-text as `Table~\ref{tab:...}`. Sized via `\resizebox` to prevent column overflow (`table*` for Tables 1, 3, 4; single-column `table` for Table 2). |
| 11 | **Bibliography style** | **PASS** | `\bibliographystyle{IEEEtran}` configured with official `IEEEtran.bst` bundled. Numbered bracketed citations (`[1]`, `[2]`). Package `cite` included for automated sorting and range compression (`[1]--[3]`). |
| 12 | **Citation consistency** | **PASS** | All 27 unique in-text `\cite{}` keys verified against `references.bib` (34 entries). Zero undefined citation keys (`missing_cites = 0`). All entries contain complete, verified metadata (authors, titles, venues, years, URLs/DOIs/arXiv IDs). |
| 13 | **Cross references** | **PASS** | All 17 in-text `\ref{}` calls correspond to defined `\label{}` targets (`missing_refs = 0`). Zero dangling, duplicated, or unnumbered cross-references. |
| 14 | **Page geometry** | **PASS** | Geometry is governed purely by `IEEEtran.cls` (3.5 in column width, 0.2 in column separation, standard margins). Package `geometry` removed to prevent layout conflicts. |
| 15 | **Font consistency** | **PASS** | Default IEEEtran font hierarchy (Times Roman family) enforced. Monospace font (`\texttt`) used consistently for code, commits, and memory tiers (`VERBATIM`, `SUMMARY`, `ARCHIVED`, `TOMBSTONE`). |
| 16 | **Figure readability** | **PASS** | Vector TikZ and PGFPlots figures generated at high resolution. Text within figures styled with `\small` / `\footnotesize` to match IEEE body typography cleanly without clipping or unreadable downscaling. |
| 17 | **Table readability** | **PASS** | Booktabs tables maintain clear vertical spacing, bold headers, and aligned decimal points for percentages and sample deviations ($\pm \sigma$). No vertical lines. |
| 18 | **No clipping** | **PASS** | Single-column figures and tables strictly bounded by `\columnwidth`. Full-width floats strictly bounded by `\textwidth`. Overfull `\hbox` eliminated. |
| 19 | **No fabricated references** | **PASS** | All 34 bibliography entries verified from primary academic sources (ACM, IEEE, NeurIPS, ICML, ICLR, ACL, arXiv). Zero hallucinations or synthetic papers. |
| 20 | **Numerical consistency** | **PASS** | All numerical values match raw benchmark outputs (`exp_canonical_run_001.json`, `exp_ablation_run_001.json`). 880 trials, 8 methods, 5 budgets. Fact Recall = 86.4%, 95% CI = [78.7%, 91.6%], 43.0% token reduction vs Full History, 100% budget compliance, -5.0% contradiction ablation, -5.0% confidence ablation, -1.0% tier ablation. |
| 21 | **Overleaf compatibility** | **PASS** | Self-contained directory structure with `IEEEtran.cls`, `IEEEtran.bst`, `PAPER.tex`, `references.bib`, `sections/`, `figures/`, `tables/`. Direct zip-upload and one-click pdfLaTeX compilation supported. |

---

## 2. Statistical Language Compliance Audit

- **Unit of Analysis:** Explicitly defined as the query-budget evaluation pair ($N = 22 \times 5 = 110$ trial pairs per method). No false claims of 110 independent dialogues.
- **Confidence Intervals:** Wilson score intervals with continuity correction ($z = 1.96, n = 110$) are presented as descriptive uncertainty bounds on the evaluated sample, without asserting universal generalization.
- **Literature Corpus Scope:** Accurately scoped to the 34 papers reviewed in the literature database, stating: *"Among the 34 papers reviewed in our literature corpus, only 5 (14.7%) explore any versioning concepts..."* rather than making unverified field-wide claims.
- **Promotional Tone Elimination:** Checked for and eliminated hyperbole (e.g., "revolutionary", "game-changing", "perfect", "100% reliable", "solves AI memory"). Objective empirical phrasing used throughout ("achieves", "demonstrates", "reduces", "is associated with").

---

## 3. Final Audit Verdict

**OVERALL AUDIT RESULT: 100% PASS (21 / 21 Criteria Met)**  
The LaTeX source code is fully compliant with IEEE conference publishing standards and prepared for Overleaf compilation.
