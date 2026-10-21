"""
Unit and integration tests for ManiGitWebService.
"""

from pathlib import Path
import tempfile
import pytest

from manigit.core.repository import ManiGitRepository
from web.backend.models import (
    ChatRequest,
    ContextPreviewRequest,
    CreateBranchRequest,
    SwitchBranchRequest,
)
from web.backend.service import ManiGitWebService


@pytest.fixture
def test_service():
    """Provides a fresh isolated ManiGitWebService with an in-memory repository."""
    repo = ManiGitRepository(db_path=":memory:")
    repo.initialize_repository()
    return ManiGitWebService(repository=repo)


def test_service_health(test_service):
    health = test_service.get_health()
    assert health["status"] == "healthy"
    assert health["active_branch"] == "main"
    assert health["head_commit_id"] is not None


def test_service_chat_and_commits(test_service):
    # Step 1: User says backend database is PostgreSQL
    req1 = ChatRequest(message="The backend database is PostgreSQL.", token_budget=1024)
    resp1 = test_service.chat(req1)
    assert resp1.turn_id is not None
    assert resp1.commit_id is not None
    c1 = resp1.commit_id

    # Check commit history
    commits = test_service.list_commits()
    assert len(commits) >= 2  # initial root + turn 1
    assert any(c.id == c1 for c in commits)

    # Active memories
    mems = test_service.get_active_memories()
    assert any("PostgreSQL" in m.content for m in mems)

    # Step 2: User supersedes with MongoDB
    req2 = ChatRequest(message="We decided to migrate the backend to MongoDB.", token_budget=1024)
    resp2 = test_service.chat(req2)
    c2 = resp2.commit_id

    # Active memories now show MongoDB
    active_mems = test_service.get_active_memories()
    assert any("MongoDB" in m.content for m in active_mems)
    assert not any("PostgreSQL" in m.content for m in active_mems)

    # Step 3: Historical checkout of c1 must show PostgreSQL (READ-ONLY)
    head_before = test_service.get_health()["head_commit_id"]
    branch_before = test_service.repository.active_branch

    hist_mems = test_service.get_commit_memories(c1)
    assert any("PostgreSQL" in m.content for m in hist_mems)
    assert not any("MongoDB" in m.content for m in hist_mems)

    # Verify active HEAD and branch are COMPLETELY UNMUTATED
    assert test_service.get_health()["head_commit_id"] == head_before
    assert test_service.repository.active_branch == branch_before

    # Step 4: Inspect Why Report for c2
    why = test_service.get_commit_why_report(c2)
    assert why is not None
    assert why.contradiction_detected is True


def test_service_branch_management(test_service):
    # Create new feature branch
    b = test_service.create_branch("feature/auth")
    assert b.name == "feature/auth"
    assert b.is_active is False

    # List branches
    branches = test_service.list_branches()
    assert len(branches) == 2
    assert any(b.name == "feature/auth" for b in branches)

    # Switch branch
    switched = test_service.switch_branch("feature/auth")
    assert switched.name == "feature/auth"
    assert switched.is_active is True
    assert test_service.repository.active_branch == "feature/auth"


def test_service_context_preview(test_service):
    # Add a memory first
    test_service.chat(ChatRequest(message="The API timeout must remain below 500 ms."))
    
    preview_req = ContextPreviewRequest(
        query="What is the API timeout?",
        token_budget=512,
    )
    preview = test_service.preview_context(preview_req)
    assert preview.token_budget == 512
    assert len(preview.selected_memories) > 0
    assert any("500 ms" in m.content for m in preview.selected_memories)
    assert preview.remaining_tokens > 0


def test_service_benchmark_summary(test_service):
    # Tests reading from actual benchmark results
    summary = test_service.get_benchmark_summary("exp_canonical_run_001")
    assert summary is not None
    assert summary.run_id == "exp_canonical_run_001"
    assert summary.total_trials == 500
    assert len(summary.methods) == 5
    assert "ManiGit (full)" in summary.method_metrics
