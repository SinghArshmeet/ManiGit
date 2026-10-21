# ManiGit: Mathematical Context Formalization & Selection Foundation

---

## 1. Abstract

This document formalizes the mathematical foundation underlying ManiGit's context compilation, memory tiering, and token budget management subsystems.

Rather than treating context compilation as an opaque heuristic or an unconstrained nearest-neighbor retrieval problem, ManiGit formalizes context assembly as a **bounded utility-maximization problem** solved deterministically via **lexical relevance ranking and greedy token-budget selection**.

---

## 2. Formal Problem Formulation

### 2.1 The Memory State
Let the active memory repository at commit $c_t$ on branch $b$ be represented as a finite set of discrete memory blocks:

$$M = \{m_1, m_2, \dots, m_n\}$$

Each memory unit $m_i \in M$ is a tuple:

$$m_i = \langle \text{id}_i, \text{content}_i, \tau_i, \sigma_i, \gamma_i, \ell_i, \Pi_i, t_i \rangle$$

where:
- $\text{id}_i \in \Sigma^+$: Unique deterministic identifier.
- $\text{content}_i \in \Sigma^*$: Textual payload of the memory unit.
- $\tau_i \in \{\text{VERBATIM}, \text{SUMMARY}, \text{ARCHIVED}, \text{TOMBSTONE}\}$: Memory tier classification.
- $\sigma_i \in \{\text{ACTIVE}, \text{SUPERSEDED}, \text{TOMBSTONE}\}$: Active lifecycle status.
- $\gamma_i \in [0.0, 1.0]$: Confidence metric assigned by rule heuristics or semantic evaluation.
- $\ell_i = L(m_i) \in \mathbb{N}^+$: Token length of the memory unit under tokenization function $L(\cdot)$.
- $\Pi_i \subseteq \mathcal{M}_{\text{raw}}$: Provenance set mapping to underlying immutable message IDs.
- $t_i \in \mathbb{R}^+$: ISO-8601 creation timestamp.

### 2.2 Token-Length Function
Let $L: \Sigma^* \to \mathbb{N}$ denote the token counting function. For any candidate subset $C \subseteq M$, the total token footprint is additive:

$$L(C) = \sum_{m_i \in C} L(m_i)$$

### 2.3 Context Budget & Hard Invariant
Given a strict inference context budget $B \in \mathbb{N}^+$, the context compilation process must select an ephemeral context subset $C_t \subseteq M$ satisfying the **Hard Budget Invariant**:

$$\sum_{m_i \in C_t} L(m_i) \le B$$

Across all possible execution paths (including $B = 0$, $L(m_i) > B$, and boundary saturation), this condition is strictly guaranteed:

$$L(C_t) \le B, \quad \forall t \ge 0$$

---

## 3. Tiered Representation Function $\Phi$

Information within ManiGit is partitioned into three discrete tiers:

$$\Phi(m_i, \tau_i) = \begin{cases}
\text{content}_i, & \text{if } \tau_i = \text{VERBATIM} \quad (\text{Tier 1}) \\
\text{summary}(\text{content}_i), & \text{if } \tau_i = \text{SUMMARY} \quad (\text{Tier 2}) \\
\emptyset, & \text{if } \tau_i \in \{\text{ARCHIVED}, \text{TOMBSTONE}\} \quad (\text{Tier 3})
\end{cases}$$

### Interpretation of Tier 3 ($\Phi(m_i, 3) = \emptyset$)
Tier 3 items have zero token weight in active prompt context ($\Phi = \emptyset$). However:
- **$\Phi = \emptyset$ denotes context exclusion, NOT physical deletion.**
- The underlying raw messages remain permanently stored in the immutable append-only SQLite archive $\mathcal{M}_{\text{raw}}$.
- Historical commit graphs and provenance pointers $\Pi_i$ remain fully intact and auditable.

---

## 4. Query Relevance Function $S(m_i, q)$

### 4.1 Lexical Relevance $S_{\text{lexical}}(m_i, q)$
The current implemented relevance function operates strictly locally and deterministically without non-deterministic external calls or embedding drift:

Let $T(s)$ denote the normalized word token multiset of string $s$ excluding language stop words. For user query $q$ and candidate memory $m_i$:

$$T_q = T(q), \quad T_{m_i} = T(\text{content}_i)$$

1. **Token Overlap Ratio**:
   $$\text{Overlap}(q, m_i) = \frac{|T_q \cap T_{m_i}|}{|T_q|}, \quad (|T_q| > 0)$$

2. **Exact Phrase Bonus**:
   $$\text{Phrase}(q, m_i) = \begin{cases} 
   0.20, & \text{if } |q| > 3 \text{ and } \text{lower}(q) \subseteq \text{lower}(\text{content}_i) \\
   0.00, & \text{otherwise}
   \end{cases}$$

3. **Combined Lexical Score**:
   $$S_{\text{lexical}}(m_i, q) = \min\left(1.0, \, \text{round}\left(0.80 \cdot \text{Overlap}(q, m_i) + \text{Phrase}(q, m_i), \, 4\right)\right)$$

If $T_q = \emptyset$, $S_{\text{lexical}}(m_i, q) = 0.0$.

---

## 5. Composite Utility Model & Relevance Dominance

### 5.1 Utility Function $U(m_i, q, t)$
The utility of admitting memory unit $m_i$ for query $q$ is modeled through a composite priority score:

$$U(m_i, q, t) = \text{Priority}(m_i, q)$$

The priority engine calculates secondary, tertiary, and quaternary signals:

$$\text{Sec}(m_i) = w_{\text{constraint}} \cdot \mathbf{1}_{\text{constraint}}(m_i) + w_{\text{decision}} \cdot \mathbf{1}_{\text{decision}}(m_i) + w_{\tau}(m_i) + w_{\text{conf}} \cdot \gamma_i$$

Default weights:
- $w_{\text{constraint}} = 0.15$
- $w_{\text{decision}} = 0.10$
- $w_{\tau}(\text{VERBATIM}) = 0.10$, $w_{\tau}(\text{SUMMARY}) = 0.05$
- $w_{\text{conf}} = 0.05$

The upper bound of secondary signals is strictly bounded:

$$\text{Sec}_{\max} = 0.15 + 0.10 + 0.10 + (0.05 \times 1.0) = \mathbf{0.40}$$

### 5.2 Mathematical Proof of Relevance Dominance
When a query contains search terms ($|T_q| > 0$):

$$\text{Priority}(m_i, q) = \begin{cases}
1.0 + \left(S_{\text{lexical}}(m_i, q) \cdot 2.0 \cdot w_{\text{rel}}\right) + \text{Sec}(m_i), & \text{if } S_{\text{lexical}}(m_i, q) > 0.0 \\
\text{Sec}(m_i) \cdot 0.10, & \text{if } S_{\text{lexical}}(m_i, q) = 0.0
\end{cases}$$

With $w_{\text{rel}} = 0.50$, the scaling factor $2.0 \cdot w_{\text{rel}} = 1.0$.

**Boundary Analysis**:
1. For any **unrelated** memory ($S_{\text{lexical}} = 0.0$):
   $$\text{Priority}_{\text{unrelated}} \le \text{Sec}_{\max} \cdot 0.10 = 0.40 \cdot 0.10 = \mathbf{0.0400}$$

2. For any **relevant** memory ($S_{\text{lexical}} > 0.0$, even minimally $S_{\text{lexical}} = 0.0001$ with zero secondary boosts):
   $$\text{Priority}_{\text{relevant}} \ge 1.0 + 0.0001 + 0.0 = \mathbf{1.0001}$$

**Theorem (Relevance Dominance)**:
$$\forall m_{\text{rel}} \in \{m \mid S_{\text{lexical}}(m, q) > 0\}, \; \forall m_{\text{unrel}} \in \{m \mid S_{\text{lexical}}(m, q) = 0\}:$$
$$\text{Priority}(m_{\text{rel}}) \ge 1.0001 > 0.0400 \ge \text{Priority}(m_{\text{unrel}})$$

**Corollaries**:
- An unrelated VERBATIM memory with maximum confidence ($\gamma = 1.0$) and explicit constraints can **never** outrank a relevant SUMMARY memory possessing query relevance.
- Relevance is the dominant partitioning factor; tier, confidence, and constraints act as secondary arbiters within relevant candidates.

---

## 6. Greedy Token-Budget Selection Algorithm

### 6.1 Total Order on Candidates
Candidates are deterministically ordered under a strict total order relation $\succ$:

$$m_a \succ m_b \iff \begin{cases}
\text{Priority}(m_a) > \text{Priority}(m_b) \\
\text{or } (\text{Priority}(m_a) = \text{Priority}(m_b) \land S(m_a, q) > S(m_b, q)) \\
\text{or } (\dots \land \gamma_a > \gamma_b) \\
\text{or } (\dots \land t_a > t_b) \\
\text{or } (\dots \land L(m_a) < L(m_b)) \\
\text{or } (\dots \land \text{id}_a < \text{id}_b)
\end{cases}$$

This guarantees bitwise deterministic ordering across repeated compilations.

### 6.2 Selection Procedure
Given sorted candidate list $(m_{(1)}, m_{(2)}, \dots, m_{(n)})$ where $m_{(i)} \succ m_{(i+1)}$:

```
Initialize:
  used_tokens ← 0
  C_t ← []
  E_t ← []

For i = 1 to n:
  If used_tokens + L(m_(i)) <= B:
    C_t.append(m_(i))
    used_tokens ← used_tokens + L(m_(i))
  Else:
    E_t.append((m_(i), reason="outside budget"))
    # CONTINUE evaluating subsequent candidates
```

**Non-Early-Termination Property**:
When candidate $m_{(i)}$ is skipped because $L(m_{(i)}) > B - \text{used\_tokens}$, evaluation continues. Smaller subsequent candidates $m_{(j)}$ ($j > i$) where $L(m_{(j)}) \le B - \text{used\_tokens}$ are admitted.

---

## 7. Computational Complexity

| Stage | Operation | Implemented Algorithm | Time Complexity | Space Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **1. State Fetch** | Reconstruct commit snapshot | Single indexed SQLite join (`commit_memories` $\bowtie$ `memories`) | $O(|M_{\text{commit}}|)$ | $O(|M_{\text{commit}}|)$ |
| **2. Relevance** | Token overlap & phrase search | Set intersection & regex scan | $O(|M| \cdot |q|)$ | $O(|M| + |q|)$ |
| **3. Priority** | Composite formula evaluation | Closed-form arithmetic | $O(|M|)$ | $O(|M|)$ |
| **4. Ordering** | Deterministic total ordering | Timsort on 6-tuple sort key | $O(|M| \log |M|)$ | $O(|M|)$ |
| **5. Budget Scan** | Greedy Token-Budget Selection | Single linear allocation pass | $O(|M|)$ | $O(|M|)$ |
| **Overall** | Context Compilation Pipeline | Full deterministic sequence | $\mathbf{O(|M_{\text{commit}}| + |M| \cdot |q| + |M| \log |M|)}$ | $\mathbf{O(|M|)}$ |

---

## 8. Why Exact Optimal Knapsack is Not Used

The 0/1 knapsack problem:

$$\max \sum_{i} U(m_i) x_i \quad \text{s.t.} \sum_{i} L(m_i) x_i \le B, \quad x_i \in \{0, 1\}$$

is NP-hard ($O(nB)$ dynamic programming pseudopolynomial complexity).

ManiGit deliberately employs **Greedy Token-Budget Selection** rather than an exact knapsack solver for the following architectural reasons:
1. **Priority Dominance**: In agent prompts, utility is dominated by relevance order. Selecting a lower-priority item merely to pack a few remaining tokens at the expense of leaving out the highest-priority relevant fact degrades agent reasoning.
2. **Deterministic & Predictable Latency**: The greedy pass runs in strictly linear $O(n)$ time after $O(n \log n)$ sorting, independent of token budget $B$.
3. **Auditability**: Skipping an item due to budget constraints is immediately explainable to users (`outside budget: requires 45 tokens, remaining 12`).

---

## 9. Architectural Extensions & Future Roadmap

### 9.1 Future Semantic Relevance $S_{\text{semantic}}(m_i, q)$
In future phases, dense vector embeddings may be introduced as an auxiliary relevance signal:

$$S_{\text{hybrid}}(m_i, q) = \lambda S_{\text{lexical}}(m_i, q) + (1 - \lambda) S_{\text{semantic}}(m_i, q)$$

The relevance dominance threshold ($\text{Priority} \ge 1.0$) will remain preserved, ensuring that vector similarity cannot override explicit deterministic safety rules.

### 9.2 Future Pinned Memory $\alpha_i \in \{0, 1\}$
Pinned memory will be formalized as a **reserved budget partition** $B_{\text{pinned}} \subseteq B$:

$$C_t = C_{\text{pinned}} \cup C_{\text{dynamic}}$$

$$\sum_{m_i \in C_{\text{pinned}}} L(m_i) \le B_{\text{pinned}}, \quad \sum_{m_j \in C_{\text{dynamic}}} L(m_j) \le B - L(C_{\text{pinned}})$$

This avoids naive unbounded constants ($\Omega = 10^6$) while mathematically guaranteeing that pinned constraints are allocated first.
