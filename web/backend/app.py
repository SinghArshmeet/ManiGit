"""
HTTP REST API server and static frontend dispatcher for ManiGit.

Implements all endpoints:
- GET  /api/health
- POST /api/chat
- GET  /api/commits
- GET  /api/commits/{commit_id}
- GET  /api/branches
- POST /api/branches
- POST /api/branches/switch
- GET  /api/memory
- GET  /api/memory/{memory_id}
- GET  /api/commits/{commit_id}/memory
- GET  /api/commits/{commit_id}/why
- POST /api/context/preview
- GET  /api/benchmarks/summary
- Static file serving from web/frontend/
"""

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from web.backend.models import (
    ChatRequest,
    ContextPreviewRequest,
    CreateBranchRequest,
    SwitchBranchRequest,
)
from web.backend.service import ManiGitWebService


class ManiGitRequestHandler(SimpleHTTPRequestHandler):
    """
    HTTP Request Handler dispatching JSON REST API routes and serving static frontend files.
    """

    service: ManiGitWebService = None
    frontend_dir: Path = Path(__file__).resolve().parent.parent / "frontend"

    def __init__(self, *args, **kwargs):
        # Set directory for static file serving
        super().__init__(*args, directory=str(self.frontend_dir), **kwargs)

    def _send_json(self, status: int, data: Any):
        """Sends a JSON response with appropriate headers."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        if hasattr(data, "model_dump"):
            payload = data.model_dump()
        elif hasattr(data, "to_dict"):
            payload = data.to_dict()
        else:
            payload = data

        self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))

    def _send_error(self, status: int, message: str):
        """Sends a structured JSON error response."""
        self._send_json(status, {"error": message, "status": status})

    def _read_json_body(self) -> Dict[str, Any]:
        """Reads and parses JSON payload from request body."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw_body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw_body)

    def do_OPTIONS(self):
        """CORS preflight handling."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Dispatches GET requests to API handlers or static files."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        # 1. API: /api/health
        if path == "/api/health":
            self._send_json(200, self.service.get_health())
            return

        # 2. API: /api/commits
        if path == "/api/commits":
            branch = query_params.get("branch", [None])[0]
            limit = int(query_params.get("limit", [50])[0])
            commits = self.service.list_commits(branch=branch, limit=limit)
            self._send_json(200, [c.model_dump() for c in commits])
            return

        # 3. API: /api/commits/{commit_id}
        m_commit = re.match(r"^/api/commits/([a-zA-Z0-9_\-]+)$", path)
        if m_commit:
            commit_id = m_commit.group(1)
            detail = self.service.get_commit(commit_id)
            if detail:
                self._send_json(200, detail)
            else:
                self._send_error(404, f"Commit '{commit_id}' not found.")
            return

        # 4. API: /api/commits/{commit_id}/memory
        m_commit_mem = re.match(r"^/api/commits/([a-zA-Z0-9_\-]+)/memory$", path)
        if m_commit_mem:
            commit_id = m_commit_mem.group(1)
            memories = self.service.get_commit_memories(commit_id)
            self._send_json(200, [m.model_dump() for m in memories])
            return

        # 5. API: /api/commits/{commit_id}/why
        m_commit_why = re.match(r"^/api/commits/([a-zA-Z0-9_\-]+)/why$", path)
        if m_commit_why:
            commit_id = m_commit_why.group(1)
            report = self.service.get_commit_why_report(commit_id)
            if report:
                self._send_json(200, report)
            else:
                self._send_error(404, f"No why report found for commit '{commit_id}'.")
            return

        # 6. API: /api/branches
        if path == "/api/branches":
            branches = self.service.list_branches()
            self._send_json(200, [b.model_dump() for b in branches])
            return

        # 7. API: /api/memory
        if path == "/api/memory":
            branch = query_params.get("branch", [None])[0]
            memories = self.service.get_active_memories(branch=branch)
            self._send_json(200, [m.model_dump() for m in memories])
            return

        # 8. API: /api/memory/{memory_id}
        m_mem = re.match(r"^/api/memory/([a-zA-Z0-9_\-]+)$", path)
        if m_mem:
            memory_id = m_mem.group(1)
            detail = self.service.get_memory_detail(memory_id)
            if detail:
                self._send_json(200, detail)
            else:
                self._send_error(404, f"Memory '{memory_id}' not found.")
            return

        # 9. API: /api/benchmarks/summary
        if path == "/api/benchmarks/summary":
            run_id = query_params.get("run_id", ["exp_canonical_run_001"])[0]
            summary = self.service.get_benchmark_summary(run_id=run_id)
            if summary:
                self._send_json(200, summary)
            else:
                self._send_error(404, f"Benchmark run '{run_id}' not found.")
            return

        # Static Frontend File Serving
        if path == "/" or not path:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        """Dispatches POST requests to API action handlers."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        try:
            body = self._read_json_body()
        except Exception as e:
            self._send_error(400, f"Malformed JSON body: {e}")
            return

        # 1. API: /api/chat
        if path == "/api/chat":
            try:
                req = ChatRequest(**body)
                response = self.service.chat(req)
                self._send_json(200, response)
            except Exception as e:
                self._send_error(400, f"Chat processing failed: {e}")
            return

        # 2. API: /api/branches (create branch)
        if path == "/api/branches":
            try:
                req = CreateBranchRequest(**body)
                branch = self.service.create_branch(req.name, req.from_commit_id)
                self._send_json(201, branch)
            except Exception as e:
                self._send_error(400, f"Failed to create branch: {e}")
            return

        # 3. API: /api/branches/switch
        if path == "/api/branches/switch":
            try:
                req = SwitchBranchRequest(**body)
                branch = self.service.switch_branch(req.branch)
                self._send_json(200, branch)
            except Exception as e:
                self._send_error(400, f"Failed to switch branch: {e}")
            return

        # 4. API: /api/context/preview
        if path == "/api/context/preview":
            try:
                req = ContextPreviewRequest(**body)
                preview = self.service.preview_context(req)
                self._send_json(200, preview)
            except Exception as e:
                self._send_error(400, f"Context preview failed: {e}")
            return

        self._send_error(404, f"API route not found: {path}")


def create_app(service: Optional[ManiGitWebService] = None, port: int = 8000) -> ThreadingHTTPServer:
    """Factory creating configured server instance."""
    ManiGitRequestHandler.service = service or ManiGitWebService()
    server = ThreadingHTTPServer(("127.0.0.1", port), ManiGitRequestHandler)
    return server
