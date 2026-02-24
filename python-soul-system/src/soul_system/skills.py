"""Skill discovery and prompt formatting.

Mirrors OpenClaw's skills/workspace.ts:
- Discover SKILL.md files in skills directories
- Parse frontmatter for metadata, invocation policy, etc.
- Format skills into a prompt block the agent can reference
"""

from __future__ import annotations

from pathlib import Path

import yaml

from soul_system.types import (
    SkillEntry,
    WorkspaceConfig,
)


def discover_skills(config: WorkspaceConfig) -> list[SkillEntry]:
    """Discover all SKILL.md files in configured skills directories.

    Looks in:
    1. workspace_dir/skills/*/SKILL.md (workspace skills)
    2. Each directory in config.skills_dirs (extra/bundled skills)

    Workspace skills override others with the same name.
    """
    merged: dict[str, SkillEntry] = {}

    # Extra/bundled skills (lower priority)
    for skills_dir in config.skills_dirs:
        for entry in _load_skills_from_dir(skills_dir):
            merged[entry.name] = entry

    # Workspace skills (highest priority)
    workspace_skills_dir = config.workspace_dir / "skills"
    for entry in _load_skills_from_dir(workspace_skills_dir):
        merged[entry.name] = entry

    return list(merged.values())


def format_skills_for_prompt(
    skills: list[SkillEntry],
    config: WorkspaceConfig,
) -> str:
    """Format skills into a prompt block for the system prompt.

    Mirrors OpenClaw's formatSkillsForPrompt() — produces a structured
    list of skills with their names, descriptions, and file paths so
    the agent knows what it can do.

    Respects max_skills_in_prompt and max_skills_prompt_chars limits.
    """
    # Filter out skills with disable_model_invocation
    visible = [s for s in skills if not s.disable_model_invocation]

    # Apply count limit
    visible = visible[: config.max_skills_in_prompt]

    if not visible:
        return ""

    lines: list[str] = ["# Available Skills", ""]
    total_chars = 0

    for skill in visible:
        block = _format_skill_block(skill)
        if total_chars + len(block) > config.max_skills_prompt_chars:
            lines.append(
                f"(truncated: showing {len(lines) - 2} of {len(visible)} skills)"
            )
            break
        lines.append(block)
        total_chars += len(block)

    return "\n".join(lines)


def _load_skills_from_dir(skills_dir: Path) -> list[SkillEntry]:
    """Load skills from a directory containing skill subdirectories."""
    entries: list[SkillEntry] = []

    if not skills_dir.is_dir():
        return entries

    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue

        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue

        try:
            entry = _parse_skill(skill_md, child)
            if entry:
                entries.append(entry)
        except Exception:
            continue  # Skip malformed skills

    return entries


def _parse_skill(skill_md: Path, base_dir: Path) -> SkillEntry | None:
    """Parse a single SKILL.md file into a SkillEntry."""
    raw = skill_md.read_text(encoding="utf-8")
    frontmatter: dict = {}
    content = raw

    if raw.startswith("---"):
        end_idx = raw.find("\n---", 3)
        if end_idx != -1:
            try:
                frontmatter = yaml.safe_load(raw[4:end_idx]) or {}
            except yaml.YAMLError:
                frontmatter = {}
            content = raw[end_idx + 4 :].lstrip()

    name = frontmatter.get("name", base_dir.name)
    description = frontmatter.get("description", "")

    # If no description in frontmatter, use first paragraph of content
    if not description and content.strip():
        first_para = content.strip().split("\n\n")[0]
        # Strip markdown headers
        lines = [
            l for l in first_para.splitlines() if not l.startswith("#")
        ]
        description = " ".join(lines).strip()[:200]

    return SkillEntry(
        name=str(name),
        description=str(description),
        file_path=skill_md,
        base_dir=base_dir,
        content=content.strip(),
        frontmatter=frontmatter,
        user_invocable=frontmatter.get("user-invocable", True),
        disable_model_invocation=frontmatter.get(
            "disable-model-invocation", False
        ),
    )


def _format_skill_block(skill: SkillEntry) -> str:
    """Format a single skill into a prompt block."""
    lines = [f"## {skill.name}"]
    if skill.description:
        lines.append(f"{skill.description}")
    lines.append(f"File: {skill.file_path}")
    if skill.user_invocable:
        lines.append(f"Invoke: /{skill.name}")
    lines.append("")
    return "\n".join(lines)
