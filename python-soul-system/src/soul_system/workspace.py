"""Workspace initialization and CLAUDE.md generation.

Creates a workspace directory with soul files and generates a CLAUDE.md that
inlines their content. The Claude Agent SDK loads CLAUDE.md automatically
when ``setting_sources=["project"]`` is set.

Like OpenClaw, the generated CLAUDE.md:
- Declares the files as **user-editable**
- Inlines each file's content under a ``## filename`` header
- Adds a SOUL.md-specific instruction to embody its persona

Workspace layout::

    workspace/
    ├── CLAUDE.md          # Auto-generated: inlines soul file contents
    ├── SOUL.md            # Agent personality & boundaries
    ├── IDENTITY.md        # Name, creature type, vibe, emoji
    ├── USER.md            # User profile
    ├── TOOLS.md           # Local tool notes
    ├── AGENTS.md          # Session guidelines & memory rules
    ├── MEMORY.md          # Long-term curated memory
    ├── BOOTSTRAP.md       # First-run onboarding (deleted after setup)
    ├── HEARTBEAT.md       # Periodic check tasks
    ├── .claude/
    │   └── skills/        # SDK-native skills
    │       └── <name>/
    │           └── SKILL.md
    └── memory/            # Daily notes (YYYY-MM-DD.md)
"""

from __future__ import annotations

import shutil
from pathlib import Path

from soul_system.types import ALL_FILENAMES, SOUL_FILENAMES, SPECIAL_FILENAMES


def get_templates_dir() -> Path:
    """Return the path to the bundled templates directory."""
    return Path(__file__).parent.parent.parent / "templates"


def ensure_workspace(
    workspace_dir: str | Path,
    *,
    seed_templates: bool = True,
) -> Path:
    """Ensure the workspace directory exists and is seeded with templates.

    Creates:
    - Template soul files (SOUL.md, IDENTITY.md, USER.md, etc.)
    - A CLAUDE.md that inlines the soul file contents
    - ``.claude/skills/`` directory for SDK-native skills
    - ``memory/`` directory for daily notes

    Returns the resolved workspace path.
    """
    workspace = Path(workspace_dir).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    if seed_templates:
        templates_dir = get_templates_dir()
        if templates_dir.is_dir():
            _seed_missing_files(workspace, templates_dir)
            _seed_skills(workspace, templates_dir)
        _ensure_claude_md(workspace)

    # Ensure directories exist
    (workspace / ".claude" / "skills").mkdir(parents=True, exist_ok=True)
    (workspace / "memory").mkdir(exist_ok=True)

    return workspace


def _seed_missing_files(workspace: Path, templates_dir: Path) -> None:
    """Copy template files into the workspace for any that are missing."""
    for name in ALL_FILENAMES:
        target = workspace / name
        if target.exists():
            continue

        template = templates_dir / name
        if template.is_file():
            shutil.copy2(template, target)


def _seed_skills(workspace: Path, templates_dir: Path) -> None:
    """Copy bundled skill templates into .claude/skills/ if not already present."""
    src_skills = templates_dir / ".claude" / "skills"
    if not src_skills.is_dir():
        return

    dst_skills = workspace / ".claude" / "skills"
    dst_skills.mkdir(parents=True, exist_ok=True)

    for skill_dir in sorted(src_skills.iterdir()):
        if not skill_dir.is_dir():
            continue
        dst_skill = dst_skills / skill_dir.name
        if dst_skill.exists():
            continue
        shutil.copytree(skill_dir, dst_skill)


def _ensure_claude_md(workspace: Path) -> None:
    """Create CLAUDE.md with inlined soul file contents if it doesn't exist."""
    claude_md = workspace / "CLAUDE.md"
    if claude_md.exists():
        return

    claude_md.write_text(generate_claude_md(workspace))


def generate_claude_md(workspace: Path) -> str:
    """Generate CLAUDE.md with inlined soul file contents.

    Mirrors OpenClaw's approach: each file's content is injected directly
    under a ``## filename`` header, with a preamble declaring them as
    user-editable.
    """
    lines: list[str] = [
        "## Workspace Files (injected)",
        "",
        "These user-editable files are loaded from the workspace and included",
        "below. Edit the source files directly — this CLAUDE.md is regenerated.",
        "",
    ]

    # Collect existing files
    has_soul = (workspace / "SOUL.md").exists()
    all_names = SOUL_FILENAMES + SPECIAL_FILENAMES
    existing = [(name, workspace / name) for name in all_names if (workspace / name).exists()]

    if not existing:
        return "\n".join(lines)

    lines.append("# Project Context")
    lines.append("")
    lines.append("The following project context files have been loaded:")

    if has_soul:
        lines.append(
            "If SOUL.md is present, embody its persona and tone. "
            "Avoid stiff, generic replies; follow its guidance unless "
            "higher-priority instructions override it."
        )

    lines.append("")

    for name, path in existing:
        content = path.read_text().strip()
        lines.append(f"## {name}")
        lines.append("")
        lines.append(content)
        lines.append("")

    return "\n".join(lines)


def refresh_claude_md(workspace_dir: str | Path) -> Path:
    """Regenerate CLAUDE.md to reflect current workspace files.

    Call this after editing soul files so the inlined content stays in sync.
    Returns the path to the generated CLAUDE.md.
    """
    workspace = Path(workspace_dir).expanduser().resolve()
    claude_md = workspace / "CLAUDE.md"
    claude_md.write_text(generate_claude_md(workspace))
    return claude_md


def is_workspace_bootstrapped(workspace_dir: str | Path) -> bool:
    """Check if the workspace has completed initial onboarding.

    A workspace is considered bootstrapped when BOOTSTRAP.md has been
    deleted (the agent deletes it after the first-run conversation).
    """
    workspace = Path(workspace_dir).expanduser().resolve()
    bootstrap = workspace / "BOOTSTRAP.md"
    identity = workspace / "IDENTITY.md"

    if not bootstrap.exists() and identity.exists():
        return True

    return False
