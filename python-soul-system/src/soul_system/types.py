"""Type definitions for the SOUL.md workspace system."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


# Soul files that get @imported into CLAUDE.md.
# These are the core workspace files loaded by the SDK via CLAUDE.md @import.
SOUL_FILENAMES: list[str] = [
    "SOUL.md",
    "IDENTITY.md",
    "USER.md",
    "TOOLS.md",
    "AGENTS.md",
    "MEMORY.md",
]

# Files that exist in the workspace but are NOT @imported into CLAUDE.md.
# BOOTSTRAP.md is deleted after onboarding; HEARTBEAT.md is for periodic tasks.
SPECIAL_FILENAMES: list[str] = [
    "BOOTSTRAP.md",
    "HEARTBEAT.md",
]

# All workspace filenames (for template seeding).
ALL_FILENAMES: list[str] = SOUL_FILENAMES + SPECIAL_FILENAMES


@dataclass
class WorkspaceConfig:
    """Configuration for the workspace."""

    workspace_dir: Path

    def __post_init__(self) -> None:
        self.workspace_dir = Path(self.workspace_dir).expanduser().resolve()
