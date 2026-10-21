"""
End-to-end HTTP REST API server tests for ManiGit Web Backend.
"""

import json
import threading
import time
from urllib.error import HTTPError
import urllib.request
import pytest

from manigit.core.repository import ManiGitRepository
from web.backend.app import create_app
from web.backend.service import ManiGitWebService


@pytest.fixture(scope="module")
def live_server():
    """Starts a live HTTP server in a daemon thread on an ephemeral port."""
    repo = ManiGitRepository(db_path=":memory:")
    repo.initialize_repository()
    service = ManiGitWebService(repository=repo)
    
    # Port 8765 for testing
    port = 8765
    server = create_app(service=service, port=port)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.1)  # wait for socket bind

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    server.server_close()


def test_http_health(live_server):
    req = urllib.request.Request(f"{live_server}/api/health")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "healthy"
        assert data["active_branch"] == "main"


def test_http_chat_flow(live_server):
    # 1. Post a user message
    payload = json.dumps({"message": "The backend database is PostgreSQL.", "token_budget": 1024}).encode("utf-8")
    req = urllib.request.Request(
        f"{live_server}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "turn_id" in data
        assert "commit_id" in data
        commit_id = data["commit_id"]

    # 2. Get commits
    req_commits = urllib.request.Request(f"{live_server}/api/commits")
    with urllib.request.urlopen(req_commits) as resp:
        assert resp.status == 200
        commits = json.loads(resp.read().decode("utf-8"))
        assert len(commits) >= 2
        assert any(c["id"] == commit_id for c in commits)

    # 3. Get active memories
    req_mem = urllib.request.Request(f"{live_server}/api/memory")
    with urllib.request.urlopen(req_mem) as resp:
        assert resp.status == 200
        memories = json.loads(resp.read().decode("utf-8"))
        assert any("PostgreSQL" in m["content"] for m in memories)

    # 4. Get historical commit memory
    req_hist = urllib.request.Request(f"{live_server}/api/commits/{commit_id}/memory")
    with urllib.request.urlopen(req_hist) as resp:
        assert resp.status == 200
        hist_mems = json.loads(resp.read().decode("utf-8"))
        assert any("PostgreSQL" in m["content"] for m in hist_mems)


def test_http_context_preview(live_server):
    payload = json.dumps({"query": "What database are we using?", "token_budget": 512}).encode("utf-8")
    req = urllib.request.Request(
        f"{live_server}/api/context/preview",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["token_budget"] == 512
        assert len(data["selected_memories"]) > 0
        assert "PostgreSQL" in data["formatted_context"]


def test_http_benchmark_summary(live_server):
    req = urllib.request.Request(f"{live_server}/api/benchmarks/summary")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["run_id"] == "exp_canonical_run_001"
        assert data["total_trials"] == 500


def test_http_static_files(live_server):
    # Test index.html
    req = urllib.request.Request(f"{live_server}/")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "ManiGit" in content
        assert "Commit Graph DAG" in content

    # Test style.css
    req_css = urllib.request.Request(f"{live_server}/style.css")
    with urllib.request.urlopen(req_css) as resp:
        assert resp.status == 200

    # Test app.js
    req_js = urllib.request.Request(f"{live_server}/app.js")
    with urllib.request.urlopen(req_js) as resp:
        assert resp.status == 200
