"""
Unit tests for web backend Pydantic API models.
"""

import pytest
from web.backend.models import (
    BenchmarkSummary,
    BranchSummary,
    ChatRequest,
    ChatResponse,
    CommitDetail,
    CommitSummary,
    ContextPreviewRequest,
    ContextPreviewResponse,
    CreateBranchRequest,
    ExcludedMemoryItem,
    MemoryDetail,
    MemorySummary,
    ProvenanceRecord,
    SelectedMemoryItem,
    SwitchBranchRequest,
    WhyReportResponse,
)


def test_chat_request_and_response_models():
    req = ChatRequest(message="Hello world", session_id="test_sess", token_budget=512)
    assert req.message == "Hello world"
    assert req.token_budget == 512

    resp = ChatResponse(
        content="Echo response",
        turn_id="turn_123",
        session_id="test_sess",
        branch="main",
        commit_id="commit_abc",
        user_message_id="msg_u1",
        assistant_message_id="msg_a1",
        context_tokens=42,
        total_tokens=90,
        created_at="2026-10-20T00:00:00Z",
    )
    assert resp.content == "Echo response"
    assert resp.context_tokens == 42


def test_commit_summary_and_detail_models():
    summary = CommitSummary(
        id="c1234567890",
        short_id="c123456",
        message="Initial state",
        author="agent",
        branch_name="main",
        memory_count=2,
        total_tokens=64,
        created_at="2026-10-20T00:00:00Z",
    )
    assert summary.short_id == "c123456"

    detail = CommitDetail(
        id="c1234567890",
        short_id="c123456",
        message="Initial state",
        author="agent",
        branch_name="main",
        memory_ids=["m1", "m2"],
        memory_count=2,
        total_tokens=64,
        created_at="2026-10-20T00:00:00Z",
    )
    assert len(detail.memory_ids) == 2


def test_context_preview_models():
    selected = SelectedMemoryItem(
        memory_id="m1",
        content="The backend database is PostgreSQL.",
        tier="VERBATIM",
        confidence=1.0,
        token_count=12,
        relevance_score=0.85,
        priority_score=0.92,
        selection_reason="High lexical query match",
    )
    excluded = ExcludedMemoryItem(
        memory_id="m2",
        content="Unrelated note",
        token_count=8,
        relevance_score=0.05,
        exclusion_reason="Low relevance",
    )
    preview = ContextPreviewResponse(
        query="What database?",
        token_budget=512,
        total_tokens=12,
        remaining_tokens=500,
        commit_id="c1",
        selected_memories=[selected],
        excluded_memories=[excluded],
        formatted_context="[Active Memory Context]\n[VERBATIM] The backend database is PostgreSQL.",
    )
    assert len(preview.selected_memories) == 1
    assert len(preview.excluded_memories) == 1
    assert preview.remaining_tokens == 500


def test_why_report_response_model():
    why = WhyReportResponse(
        commit_id="c1",
        operation="SUPERSEDE",
        tier="VERBATIM",
        confidence=0.95,
        reason="Explicit replacement of PostgreSQL with MongoDB",
        matched_rules=["decision_switch"],
        source_message_ids=["msg_1"],
        contradiction_detected=True,
        superseded_memory_id="m_old",
    )
    assert why.contradiction_detected is True
    assert why.superseded_memory_id == "m_old"
