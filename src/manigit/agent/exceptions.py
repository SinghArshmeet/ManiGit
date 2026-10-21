"""
Domain exceptions for the ManiGit Agent Runtime subsystem.
"""

from manigit.core.exceptions import ManiGitError


class AgentRuntimeError(ManiGitError):
    """Base exception for all agent runtime errors."""
    pass


class EmptyMessageError(AgentRuntimeError):
    """Raised when a user submits an empty or whitespace-only message."""
    pass


class ModelAdapterError(AgentRuntimeError):
    """Raised when the model adapter fails during generation."""
    pass


class ContextCompilationError(AgentRuntimeError):
    """Raised when context compilation fails unexpectedly."""
    pass


class InvalidBranchError(AgentRuntimeError):
    """Raised when the agent attempts to operate on a non-existent branch."""
    pass
