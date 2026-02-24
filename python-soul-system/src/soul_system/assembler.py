"""Core assembler: load workspace bootstrap files + skills into a system prompt.

This mirrors OpenClaw's workspace bootstrap pipeline:

1. Load named bootstrap files (AGENTS.md, SOUL.md, TOOLS.md, etc.)
2. Strip frontmatter from each file
3. Truncate oversized files (70% head / 20% tail) within per-file and total budgets
4. Discover skills from skills/ directories
5. Format skills into a prompt block
6. Combine everything into a system prompt string

The system prompt is then passed to the Claude Agent SDK.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from soul_system.bootstrap import (
    build_bootstrap_context,
    load_bootstrap_files,
)
from soul_system.skills import discover_skills, format_skills_for_prompt
from soul_system.types import (
    BootstrapContext,
    BootstrapFile,
    SkillEntry,
    WorkspaceConfig,
)


class SoulAssembler:
    """Assembles system prompts from workspace bootstrap files and skills.

    Mirrors OpenClaw's workspace bootstrap system:

    Workspace directory layout:
        workspace/
        ├── AGENTS.md       # Session guidelines, memory rules, safety
        ├── SOUL.md         # Agent personality and core identity
        ├── IDENTITY.md     # Name, creature type, vibe, emoji
        ├── USER.md         # Human profile (name, timezone, context)
        ├── TOOLS.md        # Local tool notes (cameras, SSH, voices)
        ├── HEARTBEAT.md    # Periodic check tasks
        ├── BOOTSTRAP.md    # First-run onboarding ritual
        ├── MEMORY.md       # Long-term curated memory
        ├── memory/         # Daily notes (YYYY-MM-DD.md)
        └── skills/         # Skill directories with SKILL.md
            ├── github/
            │   └── SKILL.md
            ├── slack/
            │   └── SKILL.md
            └── ...

    Usage:
        assembler = SoulAssembler(workspace_dir="~/.my-agent/workspace")
        system_prompt = assembler.assemble()

        # With Claude Agent SDK:
        from claude_agent_sdk import query, ClaudeAgentOptions
        async for msg in query(
            prompt="Hello",
            options=ClaudeAgentOptions(system_prompt=system_prompt),
        ):
            print(msg)
    """

    def __init__(
        self,
        workspace_dir: str | Path,
        *,
        skills_dirs: list[str | Path] | None = None,
        max_chars_per_file: int = 20_000,
        total_max_chars: int = 150_000,
        max_skills_in_prompt: int = 150,
        max_skills_prompt_chars: int = 30_000,
        extra_bootstrap_files: list[str] | None = None,
    ) -> None:
        self._config = WorkspaceConfig(
            workspace_dir=Path(workspace_dir),
            skills_dirs=[Path(d) for d in (skills_dirs or [])],
            max_chars_per_file=max_chars_per_file,
            total_max_chars=total_max_chars,
            max_skills_in_prompt=max_skills_in_prompt,
            max_skills_prompt_chars=max_skills_prompt_chars,
            extra_bootstrap_files=extra_bootstrap_files or [],
        )
        self._bootstrap_files: list[BootstrapFile] = []
        self._context_files: list[BootstrapContext] = []
        self._skills: list[SkillEntry] = []

    def load(self) -> None:
        """Load bootstrap files and skills from the workspace.

        Call this explicitly if you want to inspect files before assembling,
        or let assemble() call it automatically.
        """
        self._bootstrap_files = load_bootstrap_files(self._config)
        self._context_files = build_bootstrap_context(
            self._bootstrap_files, self._config
        )
        self._skills = discover_skills(self._config)

    def assemble(self) -> str:
        """Assemble the full system prompt from workspace files and skills.

        Automatically calls load() if not already done.
        Returns a string suitable for ClaudeAgentOptions.system_prompt.
        """
        if not self._context_files:
            self.load()

        sections: list[str] = []

        # Bootstrap context files (AGENTS.md, SOUL.md, etc.)
        for ctx in self._context_files:
            if ctx.content.strip():
                sections.append(f"<!-- {Path(ctx.path).name} -->\n{ctx.content}")

        # Skills prompt
        skills_prompt = format_skills_for_prompt(self._skills, self._config)
        if skills_prompt.strip():
            sections.append(skills_prompt)

        return "\n\n---\n\n".join(sections)

    def assemble_for_sdk(self, *, append: str | None = None) -> str | dict:
        """Assemble a system prompt for the Claude Agent SDK.

        Can return either:
        - A plain string (for custom system prompts)
        - A dict with preset + append (to extend Claude Code's built-in prompt)

        Args:
            append: Extra text to append after the assembled content.
        """
        prompt = self.assemble()
        if append:
            return f"{prompt}\n\n{append}"
        return prompt

    def assemble_with_preset(self, extra: str | None = None) -> dict:
        """Assemble as an SDK preset dict that extends Claude Code's system prompt.

        Returns a SystemPromptPreset dict for ClaudeAgentOptions.system_prompt.
        """
        prompt = self.assemble()
        if extra:
            prompt = f"{prompt}\n\n{extra}"
        return {
            "type": "preset",
            "preset": "claude_code",
            "append": prompt,
        }

    # --- Inspection methods ---

    def get_bootstrap_files(self) -> list[BootstrapFile]:
        """Return raw bootstrap files (before truncation)."""
        if not self._bootstrap_files:
            self.load()
        return list(self._bootstrap_files)

    def get_context_files(self) -> list[BootstrapContext]:
        """Return processed context files (after truncation)."""
        if not self._context_files:
            self.load()
        return list(self._context_files)

    def get_skills(self) -> list[SkillEntry]:
        """Return discovered skills."""
        if not self._skills:
            self.load()
        return list(self._skills)

    def get_file_summary(self) -> str:
        """Return a human-readable summary of loaded files."""
        if not self._context_files:
            self.load()

        lines: list[str] = ["Workspace: " + str(self._config.workspace_dir), ""]

        lines.append("Bootstrap files:")
        for f in self._bootstrap_files:
            status = "MISSING" if f.missing else f"{len(f.content or '')} chars"
            lines.append(f"  {f.name:20s} {status}")

        lines.append("")
        lines.append("Context (after truncation):")
        total = 0
        for ctx in self._context_files:
            name = Path(ctx.path).name
            trunc = " [truncated]" if ctx.truncated else ""
            lines.append(f"  {name:20s} {len(ctx.content)} chars{trunc}")
            total += len(ctx.content)
        lines.append(f"  {'TOTAL':20s} {total} chars")

        if self._skills:
            lines.append("")
            lines.append("Skills:")
            for s in self._skills:
                invoke = f" (/{s.name})" if s.user_invocable else ""
                model = " [no-model]" if s.disable_model_invocation else ""
                lines.append(f"  {s.name:20s}{invoke}{model}")

        return "\n".join(lines)
