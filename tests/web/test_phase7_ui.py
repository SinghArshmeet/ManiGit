"""
Phase 7 Verification Tests: Research Demonstration UI, DAG Graph, Historical Safety,
Explainability, Context Budgeting, and Benchmark Traceability.
"""

from pathlib import Path
import re
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
def web_service():
    """Provides a fresh isolated ManiGitWebService with an in-memory repository."""
    repo = ManiGitRepository(db_path=":memory:")
    repo.initialize_repository()
    return ManiGitWebService(repository=repo)


def test_phase7_commit_graph_dag_data(web_service):
    """
    Verifies that list_commits provides all necessary data for the visual DAG:
    - parent_commit_id for bezier edge rendering
    - branch_name for lane positioning
    - memory count, token count, short_id, author
    """
    # Create initial commit via chat
    r1 = web_service.chat(ChatRequest(message="Initial project setup: use Python 3.12."))
    c1 = r1.commit_id

    # Create child commit
    r2 = web_service.chat(ChatRequest(message="Configure SQLite for metadata."))
    c2 = r2.commit_id

    commits = web_service.list_commits()
    assert len(commits) >= 2

    # Map by ID
    c_map = {c.id: c for c in commits}
    assert c2 in c_map
    assert c1 in c_map

    # Parent relationship for DAG edge
    assert c_map[c2].parent_commit_id == c1
    assert c_map[c2].short_id == c2[:7]
    assert c_map[c2].branch_name == "main"
    assert c_map[c2].memory_count >= 1
    assert c_map[c2].total_tokens > 0


def test_phase7_historical_inspection_read_only_safety(web_service):
    """
    CRITICAL REQUIREMENT (Part 13):
    1. Inspecting historical commit does not change HEAD.
    2. Inspecting historical commit does not change branch.
    3. Inspecting historical commit does not create a commit.
    4. Inspecting historical commit does not alter memory.
    5. Returning to HEAD restores current display state.
    """
    # Turn 1: PostgreSQL
    r1 = web_service.chat(ChatRequest(message="The backend database is PostgreSQL."))
    c1 = r1.commit_id

    # Turn 2: Migrate to MongoDB (supersession)
    r2 = web_service.chat(ChatRequest(message="We decided to migrate the backend to MongoDB."))
    c2 = r2.commit_id

    # Capture repository state at HEAD
    head_before = web_service.get_health()["head_commit_id"]
    branch_before = web_service.repository.active_branch
    commit_count_before = len(web_service.list_commits())
    active_mems_before = web_service.get_active_memories()

    assert head_before == c2
    assert branch_before == "main"
    assert any("MongoDB" in m.content for m in active_mems_before)
    assert not any("PostgreSQL" in m.content for m in active_mems_before)

    # Perform Historical Inspection on C1
    hist_mems = web_service.get_commit_memories(c1)
    assert any("PostgreSQL" in m.content for m in hist_mems)
    assert not any("MongoDB" in m.content for m in hist_mems)

    # Verify repository was NOT mutated in any way
    head_after = web_service.get_health()["head_commit_id"]
    branch_after = web_service.repository.active_branch
    commit_count_after = len(web_service.list_commits())
    active_mems_after = web_service.get_active_memories()

    assert head_after == head_before
    assert branch_after == branch_before
    assert commit_count_after == commit_count_before
    assert len(active_mems_after) == len(active_mems_before)
    assert any("MongoDB" in m.content for m in active_mems_after)


def test_phase7_postgres_to_mongodb_hero_flow(web_service):
    """
    Verifies the end-to-end Hero Demonstration scenario:
    Step 1: User says "The backend database is PostgreSQL." -> C1
    Step 2: User says "We decided to migrate the backend to MongoDB." -> C2
    Step 3: User asks "What database are we using now?" -> MongoDB
    Step 4: Click C1 -> Historical state shows PostgreSQL, MongoDB absent
    Step 5: Why Report for C2 shows MongoDB superseded PostgreSQL
    Step 6: Return to HEAD -> Active state shows MongoDB
    """
    # Configure mock model adapter to generate response reflecting compiled context
    def mock_answer(prompt: str) -> str:
        if "MongoDB" in prompt:
            return "We are using MongoDB."
        if "PostgreSQL" in prompt:
            return "We are using PostgreSQL."
        return "Unknown database."

    web_service.model.generate_handler = mock_answer

    # Step 1
    r1 = web_service.chat(ChatRequest(message="The backend database is PostgreSQL."))
    c1 = r1.commit_id
    mems1 = web_service.get_commit_memories(c1)
    assert any("PostgreSQL" in m.content for m in mems1)

    # Step 2
    r2 = web_service.chat(ChatRequest(message="We decided to migrate the backend to MongoDB."))
    c2 = r2.commit_id
    active_mems2 = web_service.get_active_memories()
    assert any("MongoDB" in m.content for m in active_mems2)
    assert not any("PostgreSQL" in m.content for m in active_mems2)

    # Step 3
    r3 = web_service.chat(ChatRequest(message="What database are we using now?"))
    assert "MongoDB" in r3.content

    # Step 4 (Historical state @ C1)
    hist_mems = web_service.get_commit_memories(c1)
    assert any("PostgreSQL" in m.content for m in hist_mems)
    assert not any("MongoDB" in m.content for m in hist_mems)

    # Step 5 (Why Report @ C2)
    why_c2 = web_service.get_commit_why_report(c2)
    assert why_c2 is not None
    assert why_c2.operation == "SUPERSEDE"
    assert why_c2.contradiction_detected is True
    assert why_c2.tier == "VERBATIM"

    # Step 6 (Return to HEAD)
    head_mems = web_service.get_active_memories()
    assert any("MongoDB" in m.content for m in head_mems)


def test_phase7_why_report_fidelity(web_service):
    """
    Verifies that the Why Report provides complete explainability metadata:
    operation, tier, confidence, reason, matched rules, tokens, contradiction status.
    """
    r1 = web_service.chat(ChatRequest(message="Primary architecture constraint: 99.9% uptime required."))
    c1 = r1.commit_id

    why = web_service.get_commit_why_report(c1)
    assert why is not None
    assert why.commit_id == c1
    assert why.operation in ("RECORD", "KEEP_VERBATIM")
    assert why.tier == "VERBATIM"
    assert why.confidence > 0.8
    assert len(why.reason) > 0
    assert isinstance(why.matched_rules, list)


def test_phase7_context_preview_and_budget_meter(web_service):
    """
    Verifies ContextCompiler diagnostic preview:
    - selected memories with scores and reasons
    - excluded memories with reasons
    - exact formatted context
    - budget constraint strictly respected
    """
    # Insert multiple facts
    web_service.chat(ChatRequest(message="The database is PostgreSQL."))
    web_service.chat(ChatRequest(message="API rate limit is 100 req/sec."))
    web_service.chat(ChatRequest(message="Frontend is written in TypeScript."))

    # Preview under tight budget
    req = ContextPreviewRequest(query="What is the database and rate limit?", token_budget=128)
    prev = web_service.preview_context(req)

    assert prev.token_budget == 128
    assert prev.total_tokens <= 128
    assert prev.remaining_tokens >= 0
    assert len(prev.selected_memories) > 0
    assert prev.formatted_context is not None

    for sm in prev.selected_memories:
        assert sm.token_count > 0
        assert sm.priority_score > 0
        assert len(sm.selection_reason) > 0


def test_phase7_benchmark_aggregate_vs_budget_isolation(web_service):
    """
    Verifies Part 9:
    - Benchmark data loads from exp_canonical_run_001.json
    - Aggregate metrics and budget-specific metrics are distinct
    - Budget-specific selection (B=128) does not use aggregate numbers
    """
    summary = web_service.get_benchmark_summary(run_id="exp_canonical_run_001")
    assert summary is not None
    assert summary.total_trials == 500

    # Aggregate metrics across all budgets
    agg_mg = summary.method_metrics["ManiGit (full)"]
    assert agg_mg["avg_context_tokens"] == 179.5  # Verified aggregate value for ManiGit (full)
    assert agg_mg["fact_recall_rate"] == 0.85

    # Budget-specific metrics at B=128
    assert "128" in summary.budget_metrics
    b128_mg = summary.budget_metrics["128"]["ManiGit (full)"]
    assert b128_mg["fact_recall_rate"] == 0.85  # Verified B=128 value
    assert b128_mg["avg_context_tokens"] == 79.2  # Verified B=128 value <= 128

    # Proves aggregate and budget-specific numbers are isolated and never conflated
    assert b128_mg["avg_context_tokens"] != agg_mg["avg_context_tokens"]
    assert b128_mg["avg_context_tokens"] <= 128

    # Verify Full History aggregate (317.3) vs B=128 (109.9) isolation as well
    agg_fh = summary.method_metrics["Full History"]
    b128_fh = summary.budget_metrics["128"]["Full History"]
    assert agg_fh["avg_context_tokens"] == 317.3
    assert b128_fh["avg_context_tokens"] == 109.9
    assert b128_fh["avg_context_tokens"] != agg_fh["avg_context_tokens"]


def test_phase7_branch_visualization_data(web_service):
    """
    Verifies that branches can be created, switched, and visualized in the DAG.
    """
    # Commit on main
    r1 = web_service.chat(ChatRequest(message="Root commit on main branch."))
    c1 = r1.commit_id

    # Create and switch to experiment branch
    web_service.create_branch("experiment", from_commit_id=c1)
    web_service.switch_branch("experiment")

    # Commit on experiment branch
    r2 = web_service.chat(ChatRequest(message="Branch experimental change."))
    c2 = r2.commit_id

    # Inspect branch commits
    exp_commits = web_service.list_commits(branch="experiment")
    assert any(c.id == c2 and c.branch_name == "experiment" for c in exp_commits)

    # Switch back to main
    web_service.switch_branch("main")
    main_commits = web_service.list_commits(branch="main")
    assert any(c.id == c1 for c in main_commits)
    # c2 is on experiment, not main
    assert not any(c.id == c2 for c in main_commits)


def test_phase7_frontend_sqlite_isolation():
    """
    CRITICAL RULE:
    Verify that frontend code never directly touches SQLite, SQL strings,
    or backend files directly. All interaction must go through REST /api/.
    """
    app_js_path = Path("web/frontend/app.js")
    index_html_path = Path("web/frontend/index.html")

    assert app_js_path.exists()
    assert index_html_path.exists()

    app_js_content = app_js_path.read_text(encoding="utf-8")
    index_html_content = index_html_path.read_text(encoding="utf-8")

    # Check for direct database access violations using regexes
    forbidden_sql_patterns = [
        r"\bsqlite3\b",
        r"\bSELECT\s+.+\s+FROM\b",
        r"\bINSERT\s+INTO\b",
        r"\bUPDATE\s+\w+\s+SET\b",
        r"\bDELETE\s+FROM\b",
        r"\bDROP\s+TABLE\b",
        r"manigit\.db",
    ]

    for pat in forbidden_sql_patterns:
        assert not re.search(pat, app_js_content, re.IGNORECASE), f"Forbidden pattern '{pat}' found in app.js"
        assert not re.search(pat, index_html_content, re.IGNORECASE), f"Forbidden pattern '{pat}' found in index.html"

    # Verify all fetch calls route through /api/
    api_calls = re.findall(r'fetch\([`"\']([^`"\']+)[`"\']', app_js_content)
    assert len(api_calls) > 0
    for call in api_calls:
        assert call.startswith("/api/"), f"Frontend API call '{call}' does not route through /api/ namespace"
