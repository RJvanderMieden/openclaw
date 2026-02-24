"""Workspace initialization and management.

Mirrors OpenClaw's ensureAgentWorkspace(): creates the workspace directory
and seeds it with template files if they don't exist yet.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from soul_system.types import BOOTSTRAP_FILENAMES


def get_templates_dir() -> Path:
    """Return the path to the bundled templates directory."""
    return Path(__file__).parent.parent.parent / "templates"


def ensure_workspace(
    workspace_dir: str | Path,
    *,
    seed_templates: bool = True,
) -> Path:
    """Ensure the workspace directory exists and is seeded with templates.

    Creates the workspace directory if it doesn't exist. If seed_templates
    is True, copies template files for any that are missing.

    Returns the resolved workspace path.
    """
    workspace = Path(workspace_dir).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    if seed_templates:
        templates_dir = get_templates_dir()
        if templates_dir.is_dir():
            _seed_missing_files(workspace, templates_dir)

    # Ensure skills/ and memory/ directories exist
    (workspace / "skills").mkdir(exist_ok=True)
    (workspace / "memory").mkdir(exist_ok=True)

    return workspace


def _seed_missing_files(workspace: Path, templates_dir: Path) -> None:
    """Copy template files into the workspace for any that are missing."""
    for name in BOOTSTRAP_FILENAMES:
        target = workspace / name
        if target.exists():
            continue  # Don't overwrite existing files

        template = templates_dir / name
        if template.is_file():
            shutil.copy2(template, target)


def is_workspace_bootstrapped(workspace_dir: str | Path) -> bool:
    """Check if the workspace has completed initial onboarding.

    A workspace is considered bootstrapped when BOOTSTRAP.md has been
    deleted (the agent deletes it after the first-run conversation).
    """
    workspace = Path(workspace_dir).expanduser().resolve()
    bootstrap = workspace / "BOOTSTRAP.md"
    identity = workspace / "IDENTITY.md"

    # If BOOTSTRAP.md doesn't exist but IDENTITY.md does, onboarding is done
    if not bootstrap.exists() and identity.exists():
        return True

    # If BOOTSTRAP.md still exists, onboarding is pending
    if bootstrap.exists():
        return False

    # Workspace doesn't have either file — treat as not bootstrapped
    return False
