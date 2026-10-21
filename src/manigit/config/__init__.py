"""
Configuration module for ManiGit.

Manages application settings, database paths, model defaults,
token limits, and environment variable resolution.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path


@dataclass
class ManiGitSettings:
    """ManiGit global system settings."""

    # Base workspace directory
    base_dir: Path = field(
        default_factory=lambda: Path(os.getenv("MANIGIT_BASE_DIR", Path.cwd()))
    )

    # Database location
    db_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("MANIGIT_DB_PATH", "data/database/manigit.db")
        )
    )

    # Model settings
    model_provider: str = field(
        default_factory=lambda: os.getenv("MANIGIT_MODEL_PROVIDER", "mock")
    )
    model_name: str = field(
        default_factory=lambda: os.getenv("MANIGIT_MODEL_NAME", "gpt-4o-mini")
    )

    # Context & Token limits
    default_token_budget: int = field(
        default_factory=lambda: int(os.getenv("MANIGIT_DEFAULT_TOKEN_BUDGET", "4096"))
    )
    verbatim_window_size: int = field(
        default_factory=lambda: int(os.getenv("MANIGIT_VERBATIM_WINDOW_SIZE", "10"))
    )

    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("MANIGIT_LOG_LEVEL", "INFO")
    )


settings = ManiGitSettings()

__all__ = ["ManiGitSettings", "settings"]
