"""
ManiGit: Transparent, Versioned Context Memory for Long-Running AI Agents.

ManiGit provides a version-controlled memory architecture for AI agents:
- Raw conversation history is permanently preserved in an append-only archive.
- Agent memory is represented as a managed, versioned state.
- Changes to active memory create commits.
- Memory can be inspected, compared, branched, reconstructed, and rolled back.
- Context is assembled from memory under a token budget.
- Users can audit WHY information was retained, summarized, or archived.
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
