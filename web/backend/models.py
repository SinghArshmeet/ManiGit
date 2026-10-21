"""
Pydantic API request and response data models for ManiGit Web Interface.

Provides explicit, validated DTOs for:
- Chat / Agent Runtime
- Commit summaries & details
- Branch summaries
- Memory summaries & details
- Provenance records
- Why Reports
- Context preview
- Benchmark dashboard summaries
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================
# Chat & Agent Runtime Models
# ============================================================

class ChatRequest(BaseModel):
    """User input prompt submitted to the agent."""
    message: str
    session_id: Optional[str] = "web_session"
    branch: Optional[str] = None
    token_budget: Optional[int] = 1024


class ChatResponse(BaseModel):
    """Auditable agent response including turn metadata and active commit."""
    content: str
    turn_id: str
    session_id: str
    branch: str
    commit_id: str
    user_message_id: str
    assistant_message_id: str
    context_tokens: int
    total_tokens: int
    why_reason: Optional[str] = None
    created_at: str


# ============================================================
# Commit & DAG Models
# ============================================================

class CommitSummary(BaseModel):
    """Summary of a commit in the version graph DAG."""
    id: str
    short_id: str
    message: str
    author: str
    parent_commit_id: Optional[str] = None
    branch_name: str
    memory_count: int
    total_tokens: int
    created_at: str


class CommitDetail(BaseModel):
    """Detailed record of a specific commit."""
    id: str
    short_id: str
    message: str
    author: str
    parent_commit_id: Optional[str] = None
    branch_name: str
    memory_ids: List[str]
    memory_count: int
    total_tokens: int
    created_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# Branch Models
# ============================================================

class BranchSummary(BaseModel):
    """Branch record with current HEAD commit pointer."""
    name: str
    head_commit_id: Optional[str] = None
    is_active: bool = False
    created_at: str
    updated_at: str


class CreateBranchRequest(BaseModel):
    """Request to create a new branch."""
    name: str
    from_commit_id: Optional[str] = None


class SwitchBranchRequest(BaseModel):
    """Request to switch the active branch."""
    branch: str


# ============================================================
# Memory & Provenance Models
# ============================================================

class MemorySummary(BaseModel):
    """Summary of a memory record."""
    id: str
    tier: str
    status: str
    content: str
    confidence: float
    token_count: int
    source_message_ids: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class MemoryDetail(BaseModel):
    """Full detail of a memory record with provenance."""
    id: str
    tier: str
    status: str
    content: str
    confidence: float
    token_count: int
    source_message_ids: List[str]
    source_messages: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ProvenanceRecord(BaseModel):
    """Audit link associating a memory to a source message."""
    memory_id: str
    message_id: str
    role: str
    content: str
    created_at: str


# ============================================================
# Why Report Models
# ============================================================

class WhyReportResponse(BaseModel):
    """Explanation metadata detailing memory decisions."""
    commit_id: str
    operation: str
    tier: str
    confidence: float
    reason: str
    matched_rules: List[str] = Field(default_factory=list)
    source_message_ids: List[str] = Field(default_factory=list)
    predecessor_memory_id: Optional[str] = None
    contradiction_detected: bool = False
    superseded_memory_id: Optional[str] = None
    tokens_before: int = 0
    tokens_after: int = 0
    tokens_saved: int = 0


# ============================================================
# Context Preview Models
# ============================================================

class ContextPreviewRequest(BaseModel):
    """Request to compile a preview of context under budget."""
    query: str
    token_budget: Optional[int] = 1024
    branch: Optional[str] = None
    commit_id: Optional[str] = None


class SelectedMemoryItem(BaseModel):
    """A memory selected by ContextCompiler."""
    memory_id: str
    content: str
    tier: str
    confidence: float
    token_count: int
    relevance_score: float
    priority_score: float
    selection_reason: str
    source_message_ids: List[str] = Field(default_factory=list)


class ExcludedMemoryItem(BaseModel):
    """A memory excluded by ContextCompiler."""
    memory_id: str
    content: str
    token_count: int
    relevance_score: float
    exclusion_reason: str


class ContextPreviewResponse(BaseModel):
    """Full diagnostic view of how prompt context was assembled."""
    query: str
    token_budget: int
    total_tokens: int
    remaining_tokens: int
    commit_id: str
    branch: Optional[str] = None
    selected_memories: List[SelectedMemoryItem]
    excluded_memories: List[ExcludedMemoryItem]
    formatted_context: str


# ============================================================
# Benchmark Dashboard Models
# ============================================================

class BenchmarkSummary(BaseModel):
    """Summary of benchmark evaluation results."""
    run_id: str
    total_trials: int
    scenarios_evaluated: int
    methods: List[str]
    budgets: List[int]
    method_metrics: Dict[str, Dict[str, Any]]
    budget_metrics: Dict[str, Dict[str, Dict[str, Any]]] = Field(default_factory=dict)
    budget_vs_recall: Dict[str, Dict[str, float]]
    timestamp: str
