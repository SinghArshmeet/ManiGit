/**
 * ManiGit Research Demonstration Workstation — Frontend Application Logic
 * Phase 7: Pure modern vanilla JavaScript (Zero external framework dependencies).
 */

// ============================================================
// Explicit Frontend State Model
// ============================================================

const state = {
  activeBranch: "main",
  headCommitId: null,
  inspectingCommitId: null, // Non-null when inspecting historical state
  isHistorical: false,
  sessionId: "web_demo_session",
  tokenBudget: 1024,
  commits: [],
  memories: [],
  selectedMemoryId: null,
  benchmarkData: null,
  benchmarkMode: "aggregate", // "aggregate" | "budget"
  benchmarkBudget: 128,
  lastPreview: null,
};

// ============================================================
// API Client Layer
// ============================================================

const api = {
  async getHealth() {
    const res = await fetch("/api/health");
    if (!res.ok) throw new Error("Health check failed");
    return res.json();
  },

  async getBranches() {
    const res = await fetch("/api/branches");
    if (!res.ok) throw new Error("Failed to fetch branches");
    return res.json();
  },

  async switchBranch(branch) {
    const res = await fetch("/api/branches/switch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ branch }),
    });
    if (!res.ok) throw new Error(`Failed to switch to branch '${branch}'`);
    return res.json();
  },

  async createBranch(name, fromCommitId = null) {
    const res = await fetch("/api/branches", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, from_commit_id: fromCommitId }),
    });
    if (!res.ok) throw new Error(`Failed to create branch '${name}'`);
    return res.json();
  },

  async getCommits(branch = null) {
    const url = branch ? `/api/commits?branch=${encodeURIComponent(branch)}` : "/api/commits";
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch commits");
    return res.json();
  },

  async getCommit(commitId) {
    const res = await fetch(`/api/commits/${encodeURIComponent(commitId)}`);
    if (!res.ok) return null;
    return res.json();
  },

  async getActiveMemories(branch = null) {
    const url = branch ? `/api/memory?branch=${encodeURIComponent(branch)}` : "/api/memory";
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch memories");
    return res.json();
  },

  async getCommitMemories(commitId) {
    const res = await fetch(`/api/commits/${encodeURIComponent(commitId)}/memory`);
    if (!res.ok) throw new Error(`Failed to fetch memories for commit ${commitId}`);
    return res.json();
  },

  async getWhyReport(commitId) {
    const res = await fetch(`/api/commits/${encodeURIComponent(commitId)}/why`);
    if (!res.ok) return null;
    return res.json();
  },

  async getMemoryDetail(memoryId) {
    const res = await fetch(`/api/memory/${encodeURIComponent(memoryId)}`);
    if (!res.ok) return null;
    return res.json();
  },

  async postChat(message, budget) {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        session_id: state.sessionId,
        branch: state.activeBranch,
        token_budget: budget,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Chat request failed");
    }
    return res.json();
  },

  async postContextPreview(query, budget, commitId = null) {
    const res = await fetch("/api/context/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        token_budget: budget,
        branch: state.activeBranch,
        commit_id: commitId,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Context preview failed");
    }
    return res.json();
  },

  async getBenchmarkSummary(runId = "exp_canonical_run_001") {
    const res = await fetch(`/api/benchmarks/summary?run_id=${encodeURIComponent(runId)}`);
    if (!res.ok) return null;
    return res.json();
  },
};

// ============================================================
// Renderers & Visual Components
// ============================================================

/**
 * Renders the top branch selector dropdown.
 */
function renderBranchSelector(branches) {
  const select = document.getElementById("branch-select");
  if (!select) return;
  select.innerHTML = "";
  branches.forEach((b) => {
    const opt = document.createElement("option");
    opt.value = b.name;
    opt.textContent = b.name + (b.is_active ? " (Active)" : "");
    if (b.is_active || b.name === state.activeBranch) opt.selected = true;
    select.appendChild(opt);
  });
}

/**
 * Renders the visual Commit Graph DAG using native browser SVG and positioned HTML nodes.
 * Connects parent-child commits with clean bezier curves.
 */
function renderCommitGraph(commits) {
  state.commits = commits;
  const nodesLayer = document.getElementById("commit-nodes-layer");
  const svg = document.getElementById("commit-dag-svg");
  const countBadge = document.getElementById("commit-count-badge");
  const headChip = document.getElementById("active-head-chip");

  countBadge.textContent = `${commits.length} commits`;

  if (!commits || commits.length === 0) {
    nodesLayer.innerHTML = '<p class="placeholder-text">No commits recorded on this branch yet.</p>';
    svg.innerHTML = "";
    headChip.textContent = "none";
    updateStatusStrip();
    return;
  }

  // Active HEAD is the first commit in reverse-chronological list
  const headCommit = commits[0];
  state.headCommitId = headCommit.id;
  headChip.textContent = headCommit.short_id;

  // Build lanes for branches (main is lane 0, others assigned as encountered)
  const branchLanes = { main: 0 };
  let nextLane = 1;
  commits.forEach((c) => {
    const bName = c.branch_name || "main";
    if (branchLanes[bName] === undefined) {
      branchLanes[bName] = nextLane++;
    }
  });

  // Render HTML node rows
  nodesLayer.innerHTML = "";
  const nodeAnchors = new Map();

  commits.forEach((c) => {
    const isHead = c.id === state.headCommitId;
    const isInspected = c.id === state.inspectingCommitId;
    const lane = branchLanes[c.branch_name || "main"] || 0;
    const markerOffsetLeft = lane * 24; // indent slightly for branch lanes

    const row = document.createElement("div");
    row.className = "commit-row";
    row.dataset.commitId = c.id;

    // Node marker (anchor for SVG lines)
    const marker = document.createElement("div");
    marker.className = `commit-node-marker ${isHead ? "head-marker" : ""} ${isInspected ? "inspected-marker" : ""}`;
    marker.style.marginLeft = `${markerOffsetLeft}px`;
    marker.title = `Commit ${c.short_id} (${c.branch_name || "main"})\nClick to inspect historical state`;
    marker.addEventListener("click", () => handleCommitClick(c.id));

    // Commit Card
    const card = document.createElement("div");
    card.className = `commit-card ${isHead ? "active-head" : ""} ${isInspected ? "inspected" : ""}`;
    card.addEventListener("click", () => handleCommitClick(c.id));

    card.innerHTML = `
      <div class="commit-card-header">
        <span class="commit-id-chip">${c.short_id}</span>
        <div style="display:flex;align-items:center;gap:6px;">
          ${c.branch_name ? `<span class="commit-branch-tag">${escapeHtml(c.branch_name)}</span>` : ""}
          ${isHead ? '<span class="status-pill active" style="font-size:9.5px;">HEAD</span>' : ""}
          ${isInspected ? '<span class="status-pill" style="font-size:9.5px;background:rgba(245,158,11,0.2);color:var(--accent-amber);border:1px solid var(--accent-amber);">INSPECTING</span>' : ""}
        </div>
      </div>
      <div class="commit-card-message">${escapeHtml(c.message)}</div>
      <div class="commit-card-footer">
        <span class="chip">🕒 ${formatTime(c.created_at)}</span>
        <span class="chip">📦 ${c.memory_count} mem</span>
        <span class="chip">🪙 ${c.total_tokens} tok</span>
      </div>
    `;

    row.appendChild(marker);
    row.appendChild(card);
    nodesLayer.appendChild(row);

    nodeAnchors.set(c.id, marker);
  });

  // Draw connecting SVG paths after DOM layout settles
  requestAnimationFrame(() => {
    drawCommitGraphEdges(commits, nodeAnchors, svg);
  });

  updateStatusStrip();
}

/**
 * Draws SVG bezier lines between parent and child commit markers.
 */
function drawCommitGraphEdges(commits, nodeAnchors, svg) {
  svg.innerHTML = "";
  const viewport = document.getElementById("commit-graph-viewport");
  if (!viewport) return;

  const viewportRect = viewport.getBoundingClientRect();
  svg.setAttribute("width", viewport.scrollWidth);
  svg.setAttribute("height", viewport.scrollHeight);

  // Map each commit ID to its marker center coordinate relative to viewport
  const coords = new Map();
  nodeAnchors.forEach((marker, commitId) => {
    const rect = marker.getBoundingClientRect();
    coords.set(commitId, {
      x: rect.left - viewportRect.left + rect.width / 2 + viewport.scrollLeft,
      y: rect.top - viewportRect.top + rect.height / 2 + viewport.scrollTop,
    });
  });

  // Connect child -> parent
  commits.forEach((c) => {
    if (!c.parent_commit_id) return;
    const childCoord = coords.get(c.id);
    const parentCoord = coords.get(c.parent_commit_id);

    if (childCoord && parentCoord) {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      const x1 = childCoord.x;
      const y1 = childCoord.y;
      const x2 = parentCoord.x;
      const y2 = parentCoord.y;
      const midY = (y1 + y2) / 2;

      // Smooth vertical cubic bezier curve
      const d = `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
      path.setAttribute("d", d);
      path.setAttribute("class", "dag-edge");
      svg.appendChild(path);
    }
  });
}

/**
 * Renders memory cards with tier badges, confidence, tokens, and supersession links.
 */
function renderMemories(memories) {
  state.memories = memories;
  const container = document.getElementById("memory-list");
  const countBadge = document.getElementById("memory-count-badge");
  const alertBox = document.getElementById("superseded-alert-box");
  const alertText = document.getElementById("superseded-alert-text");

  countBadge.textContent = `${memories.length} units`;

  // Detect supersessions / contradictions among memories
  const supersededMemories = memories.filter(
    (m) => m.status === "tombstone" || (m.metadata && (m.metadata.superseded_by || m.metadata.predecessor_id))
  );

  if (supersededMemories.length > 0) {
    alertBox.classList.remove("hidden");
    alertText.innerHTML = `<strong>Contradiction / Supersession Detected:</strong> ${supersededMemories.length} memory unit(s) have recorded lineage transitions.`;
  } else {
    alertBox.classList.add("hidden");
  }

  if (memories.length === 0) {
    container.innerHTML = '<p class="placeholder-text">No memories active in this commit state.</p>';
    updateStatusStrip();
    return;
  }

  container.innerHTML = "";
  memories.forEach((m) => {
    const card = document.createElement("div");
    card.className = `memory-card ${state.selectedMemoryId === m.id ? "selected-memory" : ""}`;
    card.dataset.memoryId = m.id;

    const tierClass = m.tier.toLowerCase();
    const confPct = (m.confidence * 100).toFixed(0);

    // Check for supersession metadata
    let supersessionHtml = "";
    if (m.metadata && m.metadata.superseded_by) {
      supersessionHtml = `
        <div class="superseded-relationship-box">
          <span>↓ SUPERSEDED BY ACTIVE FACT:</span>
          <code class="mono-badge">${escapeHtml(String(m.metadata.superseded_by).slice(0, 8))}</code>
        </div>
      `;
    } else if (m.metadata && m.metadata.predecessor_id) {
      supersessionHtml = `
        <div class="superseded-relationship-box" style="background:rgba(56,189,248,0.08);color:#38bdf8;border-color:rgba(56,189,248,0.3)">
          <span>↓ SUPERSEDES PREVIOUS FACT:</span>
          <code class="mono-badge">${escapeHtml(String(m.metadata.predecessor_id).slice(0, 8))}</code>
        </div>
      `;
    }

    // Rules chips
    let rulesHtml = "";
    if (m.metadata && Array.isArray(m.metadata.matched_rules) && m.metadata.matched_rules.length > 0) {
      rulesHtml = `
        <div class="matched-rules-list" style="margin-top:4px;">
          ${m.metadata.matched_rules.map(r => `<span class="matched-rule-chip">✓ ${escapeHtml(r)}</span>`).join("")}
        </div>
      `;
    }

    card.innerHTML = `
      <div class="memory-card-header">
        <div style="display:flex;align-items:center;gap:6px;">
          <span class="tier-badge ${tierClass}">${escapeHtml(m.tier)}</span>
          <span class="status-pill ${m.status === "active" ? "active" : ""}" style="font-size:9.5px;">${escapeHtml(m.status.toUpperCase())}</span>
        </div>
        <span class="memory-conf-badge">Conf: ${confPct}%</span>
      </div>
      <div class="memory-card-content">${escapeHtml(m.content)}</div>
      ${supersessionHtml}
      ${rulesHtml}
      <div class="memory-card-footer">
        <span>🪙 ${m.token_count} tok</span>
        <span>🔗 ${m.source_message_ids.length} src msg</span>
        <span style="font-family:var(--font-mono);font-size:10px;">ID: ${m.id.slice(0, 7)}</span>
      </div>
    `;

    card.addEventListener("click", () => handleMemoryClick(m.id));
    container.appendChild(card);
  });

  updateStatusStrip();
}

/**
 * Renders the Why Report (Explainability) panel with rich metadata cards.
 */
function renderWhyReport(report, commitId) {
  const container = document.getElementById("why-report-container");
  if (!container) return;

  if (!report) {
    container.innerHTML = `
      <p class="placeholder-text">
        No explicit Why Report recorded for commit <code>${escapeHtml(commitId.slice(0, 7))}</code>.<br>
        Why Reports are automatically generated whenever memories are classified, updated, or superseded.
      </p>
    `;
    return;
  }

  const confPct = (report.confidence * 100).toFixed(1);
  const rulesList = (report.matched_rules || []).map(r => `<span class="matched-rule-chip">✓ ${escapeHtml(r)}</span>`).join("");

  container.innerHTML = `
    <div class="why-report-grid">
      <div class="why-stat-box">
        <div class="stat-label">Operation</div>
        <div class="stat-value" style="color:var(--accent-blue);">${escapeHtml(report.operation)}</div>
      </div>
      <div class="why-stat-box">
        <div class="stat-label">Assigned Tier</div>
        <div class="stat-value" style="color:var(--tier-${report.tier.toLowerCase()});">${escapeHtml(report.tier)}</div>
      </div>
      <div class="why-stat-box">
        <div class="stat-label">Confidence</div>
        <div class="stat-value">${confPct}%</div>
      </div>
      <div class="why-stat-box">
        <div class="stat-label">Contradiction Status</div>
        <div class="stat-value" style="color:${report.contradiction_detected ? "var(--accent-amber)" : "var(--text-muted)};">
          ${report.contradiction_detected ? "YES (Contradiction Superseded)" : "None"}
        </div>
      </div>
    </div>

    <div class="why-reason-box">
      <strong>Decision Rationale:</strong> ${escapeHtml(report.reason)}
    </div>

    ${rulesList ? `
      <div style="margin-top:6px;">
        <span style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;">Matched Classification Rules:</span>
        <div class="matched-rules-list">${rulesList}</div>
      </div>` : ""}

    <div style="display:flex;gap:16px;margin-top:8px;font-size:11px;color:var(--text-muted);border-top:1px solid rgba(255,255,255,0.05);padding-top:6px;">
      <span>Token Delta: <strong style="color:var(--text-primary);">${report.tokens_saved > 0 ? `-${report.tokens_saved}` : `+${report.tokens_after}`}</strong> tok</span>
      ${report.superseded_memory_id ? `<span>Superseded Memory: <code class="mono-badge">${escapeHtml(report.superseded_memory_id.slice(0, 8))}</code></span>` : ""}
      ${report.source_message_ids.length ? `<span>Source: ${report.source_message_ids.map(id => `<code class="mono-badge">${escapeHtml(id.slice(0, 8))}</code>`).join(", ")}</span>` : ""}
    </div>
  `;
}

/**
 * Renders the Context Preview with visual token budget meter, selected vs excluded breakdown,
 * and exact formatted context code block.
 */
function renderContextPreview(preview) {
  state.lastPreview = preview;
  const container = document.getElementById("context-preview-results");
  if (!container) return;

  const budget = preview.token_budget;
  const used = preview.total_tokens;
  const remaining = preview.remaining_tokens;
  const utilPct = ((used / budget) * 100).toFixed(1);

  // Sync quick header meter
  syncBudgetMeter(used, budget);

  container.innerHTML = `
    <!-- Diagnostic Meta Bar -->
    <div class="preview-meta-bar">
      <span>Query: "<strong>${escapeHtml(preview.query)}</strong>"</span>
      <span>Budget: <strong>${budget}</strong> tok</span>
      <span>Used: <strong style="color:var(--accent-green);">${used}</strong> tok</span>
      <span>Utilization: <strong>${utilPct}%</strong></span>
      <span>Commit Ref: <code>${preview.commit_id.slice(0, 7)}</code></span>
    </div>

    <!-- Visual Token Budget Meter -->
    <div class="budget-meter-card">
      <div class="budget-meter-label">
        <span>Token Budget Utilization</span>
        <span><strong>${used}</strong> / ${budget} tokens (${utilPct}%)</span>
      </div>
      <div class="meter-track" style="height:10px;margin-top:4px;">
        <div class="meter-fill" style="width: ${Math.min(100, utilPct)}%; background: ${utilPct > 90 ? "var(--accent-red)" : utilPct > 75 ? "var(--accent-amber)" : "var(--accent-green)"}"></div>
      </div>
    </div>

    <!-- Selected vs Excluded Lists -->
    <div class="preview-lists">
      <div class="preview-col">
        <h3>Selected Memories (${preview.selected_memories.length})</h3>
        ${preview.selected_memories.map(m => `
          <div class="preview-item selected">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">
              <span class="tier-badge ${m.tier.toLowerCase()}" style="font-size:9px;">${escapeHtml(m.tier)}</span>
              <span style="font-size:10px;color:var(--text-muted);">Priority: <strong>${m.priority_score.toFixed(3)}</strong> | Rel: ${m.relevance_score.toFixed(2)}</span>
            </div>
            <div style="font-size:12px;color:var(--text-primary);margin-bottom:3px;">${escapeHtml(m.content)}</div>
            <div style="color:var(--text-muted);font-size:10.5px;">
              ${m.token_count} tok | Why: ${escapeHtml(m.selection_reason)}
            </div>
          </div>
        `).join("") || '<p class="placeholder-text">Zero memories selected under budget constraint.</p>'}
      </div>

      <div class="preview-col">
        <h3>Excluded Memories (${preview.excluded_memories.length})</h3>
        ${preview.excluded_memories.map(m => `
          <div class="preview-item excluded">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">
              <span style="font-size:10.5px;color:var(--accent-red);font-weight:600;">EXCLUDED</span>
              <span style="font-size:10px;color:var(--text-muted);">Rel: ${m.relevance_score.toFixed(2)} | ${m.token_count} tok</span>
            </div>
            <div style="font-size:11.5px;color:var(--text-secondary);margin-bottom:3px;">${escapeHtml(m.content)}</div>
            <div style="color:var(--accent-amber);font-size:10.5px;">
              Reason: ${escapeHtml(m.exclusion_reason)}
            </div>
          </div>
        `).join("") || '<p class="placeholder-text">Zero memories excluded (all fit under budget).</p>'}
      </div>
    </div>

    <!-- Collapsible Formatted Context String -->
    <div class="exact-context-collapsible">
      <details>
        <summary>Exact Formatted Context Sent to Model (${used} tokens)</summary>
        <pre><code>${escapeHtml(preview.formatted_context || "(No active context compiled)")}</code></pre>
      </details>
    </div>
  `;
}

/**
 * Synchronizes the visual token budget meter in the diagnostics header and status strip.
 */
function syncBudgetMeter(used, budget) {
  const meterTokensVal = document.getElementById("meter-tokens-val");
  const meterPercentVal = document.getElementById("meter-percent-val");
  const meterFill = document.getElementById("meter-fill");
  const stripContextTokens = document.getElementById("strip-context-tokens");

  if (!meterTokensVal || !meterPercentVal || !meterFill) return;

  const pct = Math.min(100, (used / budget) * 100).toFixed(1);
  meterTokensVal.textContent = `${used} / ${budget}`;
  meterPercentVal.textContent = `${pct}%`;
  meterFill.style.width = `${pct}%`;
  meterFill.style.backgroundColor = pct > 90 ? "var(--accent-red)" : pct > 75 ? "var(--accent-amber)" : "var(--accent-green)";

  if (stripContextTokens) {
    stripContextTokens.textContent = `${used} tok`;
  }
}

/**
 * Renders the Benchmark Dashboard with both aggregate and budget-specific tables,
 * backed 100% by backend exp_canonical_run_001.json empirical data.
 */
function renderBenchmarks(summary) {
  state.benchmarkData = summary;
  const container = document.getElementById("benchmark-summary-container");
  if (!container) return;

  if (!summary) {
    container.innerHTML = '<p class="placeholder-text">No benchmark run data loaded from backend.</p>';
    return;
  }

  const isAggregate = state.benchmarkMode === "aggregate";
  const budgetKey = String(state.benchmarkBudget);

  let tableTitle = "";
  let rowsData = [];

  if (isAggregate) {
    tableTitle = `Across All Budgets (Average over B=128, 256, 512, 1024, 2048) — ${summary.total_trials} Empirical Trials`;
    rowsData = Object.entries(summary.method_metrics).map(([method, d]) => ({
      method,
      factRecall: (d.fact_recall_rate * 100).toFixed(1) + "%",
      answerCorrect: (d.answer_correctness_rate * 100).toFixed(1) + "%",
      histRecall: d.historical_recall_rate !== null ? (d.historical_recall_rate * 100).toFixed(1) + "%" : "N/A",
      avgCtxTokens: d.avg_context_tokens,
      utilization: (d.avg_context_utilization * 100).toFixed(1) + "%",
      latency: d.avg_latency_context_ms + " ms",
    }));
  } else {
    tableTitle = `Budget-Specific (Budget = ${budgetKey} Tokens) — Empirical Run exp_canonical_run_001`;
    const bMetrics = (summary.budget_metrics && summary.budget_metrics[budgetKey]) || {};
    rowsData = Object.entries(bMetrics).map(([method, d]) => ({
      method,
      factRecall: (d.fact_recall_rate * 100).toFixed(1) + "%",
      answerCorrect: (d.answer_correctness_rate * 100).toFixed(1) + "%",
      histRecall: d.historical_recall_rate !== null ? (d.historical_recall_rate * 100).toFixed(1) + "%" : "N/A",
      avgCtxTokens: d.avg_context_tokens,
      utilization: (d.avg_context_utilization * 100).toFixed(1) + "%",
      latency: d.avg_latency_context_ms + " ms",
    }));
  }

  const tableRows = rowsData.map(r => `
    <tr class="${r.method === "ManiGit" ? "highlight-row" : ""}">
      <td><strong>${escapeHtml(r.method)}</strong></td>
      <td><strong>${r.factRecall}</strong></td>
      <td>${r.answerCorrect}</td>
      <td>${r.histRecall}</td>
      <td><span class="mono">${r.avgCtxTokens}</span></td>
      <td>${r.utilization}</td>
      <td>${r.latency}</td>
    </tr>
  `).join("");

  // Lightweight visual bar chart comparing Fact Recall
  const chartBars = rowsData.map(r => {
    const val = parseFloat(r.factRecall) || 0;
    const isManiGit = r.method === "ManiGit";
    return `
      <div class="chart-bar-col" style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;">
        <span style="font-size:10.5px;font-weight:600;color:${isManiGit ? "var(--accent-blue)" : "var(--text-secondary)}">${val.toFixed(1)}%</span>
        <div style="width:100%;height:60px;background:rgba(255,255,255,0.04);border-radius:3px;display:flex;align-items:flex-end;">
          <div style="width:100%;height:${val}%;background:${isManiGit ? "var(--accent-blue)" : "#475569"};border-radius:2px;transition:height 0.3s ease;"></div>
        </div>
        <span style="font-size:10px;color:var(--text-muted);text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:70px;">${escapeHtml(r.method)}</span>
      </div>
    `;
  }).join("");

  container.innerHTML = `
    <div style="margin-bottom:10px;">
      <span style="font-size:11.5px;font-weight:600;color:var(--accent-blue);">${escapeHtml(tableTitle)}</span>
    </div>

    <table class="benchmark-table">
      <thead>
        <tr>
          <th>Method</th>
          <th>Fact Recall</th>
          <th>Answer Correct</th>
          <th>Historical Recall</th>
          <th>Avg Context Tokens</th>
          <th>Utilization</th>
          <th>Latency</th>
        </tr>
      </thead>
      <tbody>
        ${tableRows}
      </tbody>
    </table>

    <!-- Comparative Bar Chart -->
    <div class="benchmark-chart-box" style="margin-top:14px;background:var(--bg-darkest);border:1px solid var(--border-subtle);border-radius:6px;padding:10px 14px;">
      <div style="font-size:11px;font-weight:600;color:var(--text-secondary);margin-bottom:8px;">Fact Recall Comparison (${isAggregate ? "Across All Budgets" : `Budget = ${budgetKey}`})</div>
      <div style="display:flex;gap:12px;align-items:flex-end;height:80px;">
        ${chartBars}
      </div>
    </div>
  `;
}

/**
 * Renders the Provenance Traceability View for the selected memory.
 */
async function renderProvenance(memoryId) {
  const container = document.getElementById("provenance-container");
  if (!container) return;

  if (!memoryId) {
    container.innerHTML = `
      <p class="placeholder-text">
        Click on any memory card in the Memory Inspector to trace its end-to-end lineage:<br>
        Memory Unit → Source Message(s) → Classification Decision → Commit DAG → Current / Historical State.
      </p>
    `;
    return;
  }

  container.innerHTML = '<p class="placeholder-text">Tracing provenance lineage from repository...</p>';

  try {
    const detail = await api.getMemoryDetail(memoryId);
    if (!detail) {
      container.innerHTML = `<p class="placeholder-text" style="color:var(--accent-red)">Memory '${escapeHtml(memoryId)}' not found in repository.</p>`;
      return;
    }

    const sources = detail.source_messages || [];
    const sourceHtml = sources.length > 0
      ? sources.map(s => `
          <div class="prov-source-card" style="background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:4px;padding:6px 10px;margin-top:4px;">
            <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text-muted);">
              <span>Role: <strong>${escapeHtml(s.role)}</strong></span>
              <span class="mono">ID: ${s.id.slice(0, 8)}</span>
            </div>
            <div style="font-size:12px;color:var(--text-primary);margin-top:2px;">${escapeHtml(s.content)}</div>
          </div>
        `).join("")
      : `<span style="color:var(--text-muted);font-size:11px;">(Source message ID: ${detail.source_message_ids.join(", ")})</span>`;

    container.innerHTML = `
      <div class="provenance-chain">
        <!-- Node 1: Memory Unit -->
        <div class="prov-node">
          <div class="prov-node-header">
            <span class="prov-node-title">1. Memory Unit</span>
            <span class="tier-badge ${detail.tier.toLowerCase()}" style="font-size:9px;">${escapeHtml(detail.tier)}</span>
          </div>
          <div class="prov-node-body">
            <strong>Content:</strong> "${escapeHtml(detail.content)}"<br>
            <span style="font-size:10.5px;color:var(--text-muted);">Confidence: ${(detail.confidence * 100).toFixed(0)}% | Tokens: ${detail.token_count}</span>
          </div>
        </div>

        <div class="prov-arrow">↓ Generated From</div>

        <!-- Node 2: Source Messages -->
        <div class="prov-node">
          <div class="prov-node-header">
            <span class="prov-node-title">2. Source Message(s) Provenance</span>
            <span class="mono" style="font-size:10px;color:var(--accent-blue);">${sources.length} message(s)</span>
          </div>
          <div class="prov-node-body">
            ${sourceHtml}
          </div>
        </div>

        <div class="prov-arrow">↓ Audited In Commit</div>

        <!-- Node 3: Commit Record -->
        <div class="prov-node">
          <div class="prov-node-header">
            <span class="prov-node-title">3. Versioned Commit Snapshot</span>
            <span class="mono" style="font-size:10px;color:var(--accent-green);">${detail.created_at ? formatTime(detail.created_at) : "audited"}</span>
          </div>
          <div class="prov-node-body">
            <strong>Branch:</strong> <span class="mono">${escapeHtml(state.activeBranch)}</span><br>
            <strong>State:</strong> <span class="status-pill ${detail.status === "active" ? "active" : ""}" style="font-size:9.5px;">${escapeHtml(detail.status.toUpperCase())}</span>
            ${detail.metadata && detail.metadata.superseded_by ? `<br><strong style="color:var(--accent-red);">Superseded By:</strong> <code class="mono-badge">${escapeHtml(String(detail.metadata.superseded_by).slice(0, 8))}</code>` : ""}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p class="placeholder-text" style="color:var(--accent-red)">Provenance error: ${escapeHtml(err.message)}</p>`;
  }
}

/**
 * Updates the persistent status strip at the bottom of the workstation.
 */
function updateStatusStrip() {
  const stripBranch = document.getElementById("strip-branch");
  const stripHead = document.getElementById("strip-head");
  const stripBudget = document.getElementById("strip-budget");
  const stripMemCount = document.getElementById("strip-mem-count");
  const stripStatus = document.getElementById("strip-status");
  const activeBranchChip = document.getElementById("active-branch-chip");

  if (stripBranch) stripBranch.textContent = state.activeBranch;
  if (activeBranchChip) activeBranchChip.textContent = state.activeBranch;
  if (stripHead) stripHead.textContent = state.headCommitId ? state.headCommitId.slice(0, 7) : "—";
  if (stripBudget) stripBudget.textContent = `${state.tokenBudget} tok`;
  if (stripMemCount) stripMemCount.textContent = state.memories ? state.memories.length : "0";

  if (stripStatus) {
    if (state.isHistorical) {
      stripStatus.textContent = `Historical (${state.inspectingCommitId ? state.inspectingCommitId.slice(0, 7) : ""})`;
      stripStatus.className = "strip-val amber";
    } else {
      stripStatus.textContent = "Ready (HEAD)";
      stripStatus.className = "strip-val green";
    }
  }
}

/**
 * Appends a user or assistant chat message to the Agent Dialogue transcript.
 */
function appendChatMessage(role, content, meta = null) {
  const container = document.getElementById("chat-messages");
  if (!container) return;

  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${role === "user" ? "user-msg" : role === "assistant" ? "assistant-msg" : "system-msg"}`;

  let metaHtml = "";
  if (meta) {
    metaHtml = `
      <div class="msg-meta">
        ${meta.commit_id ? `<span>Ref: <code class="mono">${meta.commit_id.slice(0, 7)}</code></span>` : ""}
        ${meta.context_tokens !== undefined ? `<span>Ctx: <strong>${meta.context_tokens}</strong> tok</span>` : ""}
        ${meta.why_reason ? `<span>💡 ${escapeHtml(meta.why_reason)}</span>` : ""}
      </div>
    `;
  }

  msgDiv.innerHTML = `
    <div class="msg-content">${escapeHtml(content)}</div>
    ${metaHtml}
  `;
  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

// ============================================================
// Event Handlers & User Interactions
// ============================================================

/**
 * Handles clicking a commit in the DAG.
 * Enters read-only historical inspection without mutating repo state.
 */
async function handleCommitClick(commitId) {
  state.inspectingCommitId = commitId;
  const isHead = commitId === state.headCommitId;
  state.isHistorical = !isHead;

  const banner = document.getElementById("historical-banner");
  const returnHeadTopBtn = document.getElementById("return-head-top-btn");
  const inspectingIdBadge = document.getElementById("inspecting-commit-id");
  const inspectingMeta = document.getElementById("inspecting-commit-meta");
  const memHeading = document.getElementById("memory-panel-heading");

  if (isHead) {
    banner.classList.add("hidden");
    returnHeadTopBtn.classList.add("hidden");
    memHeading.textContent = "Active Memories";
  } else {
    banner.classList.remove("hidden");
    returnHeadTopBtn.classList.remove("hidden");
    inspectingIdBadge.textContent = commitId.slice(0, 7);

    // Find parent and branch
    const cObj = state.commits.find(c => c.id === commitId);
    const parentText = cObj && cObj.parent_commit_id ? `Parent: ${cObj.parent_commit_id.slice(0, 7)}` : "Root Commit";
    const branchText = cObj && cObj.branch_name ? `Branch: ${cObj.branch_name}` : `Branch: ${state.activeBranch}`;
    inspectingMeta.textContent = `| ${parentText} | ${branchText}`;
    memHeading.textContent = `Historical Memories @ ${commitId.slice(0, 7)}`;
  }

  // Re-render commit graph highlights
  renderCommitGraph(state.commits);

  // Load historical memories via dedicated read-only API
  try {
    const memories = await api.getCommitMemories(commitId);
    renderMemories(memories);
  } catch (err) {
    console.error("Failed to load historical memories:", err);
  }

  // Load Why Report for this commit
  try {
    const report = await api.getWhyReport(commitId);
    renderWhyReport(report, commitId);
  } catch (err) {
    renderWhyReport(null, commitId);
  }

  // If inspection occurs, switch bottom tab to Why Report so user sees explanation immediately
  if (!isHead) {
    switchDiagnosticsTab("tab-why");
  }

  updateStatusStrip();
}

/**
 * Returns from historical inspection to active HEAD state.
 */
async function handleReturnToHead() {
  state.inspectingCommitId = null;
  state.isHistorical = false;

  document.getElementById("historical-banner").classList.add("hidden");
  document.getElementById("return-head-top-btn").classList.add("hidden");
  document.getElementById("memory-panel-heading").textContent = "Active Memories";

  renderCommitGraph(state.commits);
  const memories = await api.getActiveMemories(state.activeBranch);
  renderMemories(memories);

  updateStatusStrip();
}

/**
 * Handles clicking a memory card to inspect provenance.
 */
function handleMemoryClick(memoryId) {
  state.selectedMemoryId = memoryId;
  // Re-highlight cards
  document.querySelectorAll(".memory-card").forEach((c) => {
    c.classList.toggle("selected-memory", c.dataset.memoryId === memoryId);
  });

  // Switch to provenance tab and render
  switchDiagnosticsTab("tab-provenance");
  renderProvenance(memoryId);
}

/**
 * Switches the active diagnostics panel tab.
 */
function switchDiagnosticsTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-pane").forEach((p) => {
    p.classList.toggle("active", p.id === tabId);
  });
}

/**
 * Submits user chat prompt to the agent runtime.
 */
async function handleChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;

  const budget = parseInt(document.getElementById("token-budget-input").value) || 1024;
  state.tokenBudget = budget;
  input.value = "";

  appendChatMessage("user", text);

  try {
    const res = await api.postChat(text, budget);
    appendChatMessage("assistant", res.content, {
      commit_id: res.commit_id,
      context_tokens: res.context_tokens,
      why_reason: res.why_reason,
    });

    // Update quick meter
    syncBudgetMeter(res.context_tokens, budget);

    // Refresh DAG commits and active memories
    await refreshState();
  } catch (err) {
    appendChatMessage("system", `Error: ${err.message}`);
  }
}

/**
 * Executes a ContextCompiler diagnostic preview run.
 */
async function handlePreviewRun() {
  const input = document.getElementById("preview-query-input");
  const query = input.value.trim();
  if (!query) return;

  const budgetSelect = document.getElementById("preview-budget-select");
  const budget = parseInt(budgetSelect ? budgetSelect.value : "1024") || 1024;
  const targetCommit = state.inspectingCommitId || state.headCommitId;

  try {
    const preview = await api.postContextPreview(query, budget, targetCommit);
    renderContextPreview(preview);
  } catch (err) {
    const container = document.getElementById("context-preview-results");
    if (container) {
      container.innerHTML = `<p class="placeholder-text" style="color:var(--accent-red)">Error: ${escapeHtml(err.message)}</p>`;
    }
  }
}

/**
 * Refreshes repository state from backend (commits, memories, branches).
 */
async function refreshState() {
  try {
    const commits = await api.getCommits(state.activeBranch);
    renderCommitGraph(commits);

    if (!state.inspectingCommitId) {
      const memories = await api.getActiveMemories(state.activeBranch);
      renderMemories(memories);
    }
  } catch (err) {
    console.error("Refresh state failed:", err);
  }
}

// ============================================================
// Initialization & Lifecycle
// ============================================================

async function init() {
  // Tab switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      switchDiagnosticsTab(btn.dataset.tab);
    });
  });

  // Chat submit form
  const chatForm = document.getElementById("chat-form");
  if (chatForm) chatForm.addEventListener("submit", handleChatSubmit);

  // Return to HEAD buttons
  const returnHeadBtn = document.getElementById("return-head-btn");
  if (returnHeadBtn) returnHeadBtn.addEventListener("click", handleReturnToHead);

  const returnHeadTopBtn = document.getElementById("return-head-top-btn");
  if (returnHeadTopBtn) returnHeadTopBtn.addEventListener("click", handleReturnToHead);

  // Refresh button
  const refreshBtn = document.getElementById("refresh-btn");
  if (refreshBtn) refreshBtn.addEventListener("click", refreshState);

  // New session button
  const newSessionBtn = document.getElementById("new-session-btn");
  if (newSessionBtn) {
    newSessionBtn.addEventListener("click", () => {
      state.sessionId = `session_${Date.now()}`;
      const chatMessages = document.getElementById("chat-messages");
      if (chatMessages) {
        chatMessages.innerHTML = `
          <div class="message system-msg">
            <div class="msg-content">
              <strong>New Session Initialized (<code>${state.sessionId}</code>).</strong><br>
              Enter instructions below or use the hero demo pills.
            </div>
          </div>
        `;
      }
    });
  }

  // Token budget selector in chat panel
  const tokenBudgetInput = document.getElementById("token-budget-input");
  if (tokenBudgetInput) {
    tokenBudgetInput.addEventListener("change", (e) => {
      state.tokenBudget = parseInt(e.target.value) || 1024;
      updateStatusStrip();
    });
  }

  // Diagnostic context preview button
  const runPreviewBtn = document.getElementById("run-preview-btn");
  if (runPreviewBtn) runPreviewBtn.addEventListener("click", handlePreviewRun);

  // Hero Demo Pills
  document.querySelectorAll(".pill-btn").forEach((pill) => {
    pill.addEventListener("click", () => {
      const prompt = pill.dataset.prompt;
      if (prompt) {
        const input = document.getElementById("chat-input");
        if (input) {
          input.value = prompt;
          input.focus();
        }
      }
    });
  });

  // Benchmark Mode Toggle
  const benchModeAggregate = document.getElementById("bench-mode-aggregate");
  const benchModeBudget = document.getElementById("bench-mode-budget");
  const benchBudgetSelectorGroup = document.getElementById("bench-budget-selector-group");
  const benchBudgetSelect = document.getElementById("bench-budget-select");

  if (benchModeAggregate && benchModeBudget) {
    benchModeAggregate.addEventListener("click", () => {
      state.benchmarkMode = "aggregate";
      benchModeAggregate.classList.add("active");
      benchModeBudget.classList.remove("active");
      if (benchBudgetSelectorGroup) benchBudgetSelectorGroup.classList.add("hidden");
      renderBenchmarks(state.benchmarkData);
    });

    benchModeBudget.addEventListener("click", () => {
      state.benchmarkMode = "budget";
      benchModeBudget.classList.add("active");
      benchModeAggregate.classList.remove("active");
      if (benchBudgetSelectorGroup) benchBudgetSelectorGroup.classList.remove("hidden");
      renderBenchmarks(state.benchmarkData);
    });
  }

  if (benchBudgetSelect) {
    benchBudgetSelect.addEventListener("change", (e) => {
      state.benchmarkBudget = parseInt(e.target.value) || 128;
      renderBenchmarks(state.benchmarkData);
    });
  }

  // Branch selector dropdown
  const branchSelect = document.getElementById("branch-select");
  if (branchSelect) {
    branchSelect.addEventListener("change", async (e) => {
      const branchName = e.target.value;
      try {
        await api.switchBranch(branchName);
        state.activeBranch = branchName;
        state.inspectingCommitId = null;
        state.isHistorical = false;
        document.getElementById("historical-banner").classList.add("hidden");
        document.getElementById("return-head-top-btn").classList.add("hidden");
        await refreshState();
      } catch (err) {
        alert(err.message);
      }
    });
  }

  // Create new branch button
  const newBranchBtn = document.getElementById("new-branch-btn");
  if (newBranchBtn) {
    newBranchBtn.addEventListener("click", async () => {
      const name = prompt("Enter new branch name (e.g. experiment):");
      if (!name || !name.trim()) return;
      try {
        await api.createBranch(name.trim());
        await api.switchBranch(name.trim());
        state.activeBranch = name.trim();
        const branches = await api.getBranches();
        renderBranchSelector(branches);
        await refreshState();
      } catch (err) {
        alert(err.message);
      }
    });
  }

  // Handle window resizing to redraw SVG edges cleanly
  window.addEventListener("resize", () => {
    if (state.commits && state.commits.length > 0) {
      renderCommitGraph(state.commits);
    }
  });

  // Initial Data Fetch
  try {
    const health = await api.getHealth();
    if (health.active_branch) {
      state.activeBranch = health.active_branch;
    }
  } catch (e) {
    console.warn("Health check error:", e);
  }

  try {
    const branches = await api.getBranches();
    renderBranchSelector(branches);
  } catch (e) {
    console.warn("Branches fetch error:", e);
  }

  await refreshState();

  try {
    const benchmarks = await api.getBenchmarkSummary();
    renderBenchmarks(benchmarks);
  } catch (e) {
    console.warn("Benchmarks fetch error:", e);
  }
}

// ============================================================
// Utilities
// ============================================================

function escapeHtml(text) {
  if (text === null || text === undefined) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatTime(isoString) {
  if (!isoString) return "";
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch (e) {
    return isoString;
  }
}

document.addEventListener("DOMContentLoaded", init);
