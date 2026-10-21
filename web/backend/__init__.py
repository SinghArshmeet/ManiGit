"""
ManiGit Web Backend Package.
"""

import sys
from pathlib import Path

# Ensure src is in sys.path for direct module execution
_src_path = str(Path(__file__).resolve().parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

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
    MemoryDetail,
    MemorySummary,
    ProvenanceRecord,
    SwitchBranchRequest,
    WhyReportResponse,
)
from web.backend.service import ManiGitWebService
from web.backend.app import create_app, ManiGitRequestHandler

__all__ = [
    "ManiGitWebService",
    "create_app",
    "ManiGitRequestHandler",
    "ChatRequest",
    "ChatResponse",
    "CommitSummary",
    "CommitDetail",
    "BranchSummary",
    "CreateBranchRequest",
    "SwitchBranchRequest",
    "MemorySummary",
    "MemoryDetail",
    "ProvenanceRecord",
    "WhyReportResponse",
    "ContextPreviewRequest",
    "ContextPreviewResponse",
    "BenchmarkSummary",
]
