"""
Core exception classes for the ManiGit repository.
"""


class ManiGitError(Exception):
    """Base exception for all ManiGit errors."""


class RepositoryError(ManiGitError):
    """General repository operational error."""


class DatabaseError(RepositoryError):
    """Underlying database or SQLite failure."""


class MessageNotFoundError(RepositoryError):
    """Raised when a requested message ID does not exist."""


class MemoryNotFoundError(RepositoryError):
    """Raised when a requested memory ID does not exist."""


class CommitNotFoundError(RepositoryError):
    """Raised when a requested commit ID does not exist."""


class BranchNotFoundError(RepositoryError):
    """Raised when a requested branch does not exist."""


class BranchAlreadyExistsError(RepositoryError):
    """Raised when attempting to create a branch that already exists."""


class ImmutableRecordError(RepositoryError):
    """Raised when an attempt is made to mutate an immutable record."""


class InvalidCommitError(RepositoryError):
    """Raised when a commit has invalid structure, missing parent, or invalid memory items."""
