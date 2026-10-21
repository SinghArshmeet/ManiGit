"""
Core domain models and value objects for the ManiGit repository.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import json


class MessageRole(str, Enum):
    """Supported roles for raw conversation messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MemoryTier(str, Enum):
    """Storage tiers for version-controlled agent memory."""
    VERBATIM = "VERBATIM"
    SUMMARY = "SUMMARY"
    ARCHIVED = "ARCHIVED"
    TOMBSTONE = "TOMBSTONE"


class MemoryStatus(str, Enum):
    """Lifecycle status of a memory record."""
    ACTIVE = "ACTIVE"
    TOMBSTONE = "TOMBSTONE"


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Message:
    """
    Represents an immutable raw conversation event.
    
    A message must never be overwritten or deleted as part of memory management.
    """
    id: str
    session_id: str
    role: str
    content: str
    sequence_num: int
    token_count: int
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "sequence_num": self.sequence_num,
            "token_count": self.token_count,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class Memory:
    """
    Represents a piece of knowledge derived from raw conversation messages.
    
    Supports provenance linking to multiple source message IDs.
    """
    id: str
    content: str
    tier: str
    status: str
    confidence: float
    token_count: int
    source_message_ids: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "tier": self.tier,
            "status": self.status,
            "confidence": self.confidence,
            "token_count": self.token_count,
            "source_message_ids": list(self.source_message_ids),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class Commit:
    """
    Represents an immutable, versioned change to the active memory state.
    """
    id: str
    parent_commit_id: Optional[str]
    branch: str
    message: str
    reason: str
    token_count_before: int
    token_count_after: int
    tokens_saved: int
    author: str = "agent:auto"
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "parent_commit_id": self.parent_commit_id,
            "branch": self.branch,
            "message": self.message,
            "reason": self.reason,
            "author": self.author,
            "token_count_before": self.token_count_before,
            "token_count_after": self.token_count_after,
            "tokens_saved": self.tokens_saved,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class Branch:
    """
    Represents a named pointer to a commit in the repository.
    """
    name: str
    head_commit_id: Optional[str]
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "head_commit_id": self.head_commit_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
