"""Claude Agent SDK integration for the SOUL.md workspace system.

How this relates to the SDK's built-in setting_sources
------------------------------------------------------

The Claude Agent SDK has a ``setting_sources`` parameter that controls what
it loads from the filesystem automatically:

- ``setting_sources=None`` (default): SDK loads NOTHING from disk.
- ``setting_sources=["project"]``: SDK auto-loads CLAUDE.md files and
  ``.claude/settings.json`` (including ``.claude/skills/``).
- ``setting_sources=["user", "project", "local"]``: Full Claude Code experience.

That system handles **project coding instructions** (CLAUDE.md) and **Claude
Code skills** (``.claude/skills/``). It does NOT know about the SOUL.md
workspace concept — agent personality, identity, memory, user profile, etc.

This module bridges the two:

1. **Custom prompt mode** (``use_preset=False``, default):
   Assembles the SOUL.md workspace into a standalone system prompt.
   Use when your agent's entire personality comes from the workspace.
   Combine with ``setting_sources=["project"]`` so the SDK also picks up
   CLAUDE.md and ``.claude/skills/`` on top.

2. **Preset mode** (``use_preset=True``):
   Appends the SOUL.md workspace content to Claude Code's built-in system
   prompt via ``{"type": "preset", "preset": "claude_code", "append": ...}``.
   Use when you want Claude Code's full behavior plus workspace personality.

In both modes, ``setting_sources`` is orthogonal — it controls whether the SDK
also loads CLAUDE.md/skills from disk, independent of the SOUL.md workspace.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncIterator

from soul_system.assembler import SoulAssembler

# SDK imports are deferred so tests can run without the SDK installed.
try:
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        query as sdk_query,
    )
    from claude_agent_sdk.types import AgentDefinition

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


def create_soul_options(
    workspace_dir: str | Path,
    *,
    skills_dirs: list[str | Path] | None = None,
    allowed_tools: list[str] | None = None,
    permission_mode: str = "acceptEdits",
    use_preset: bool = False,
    extra_instructions: str | None = None,
    model: str | None = None,
    setting_sources: list[str] | None = None,
    include_soul_agents: bool = False,
    **kwargs: Any,
) -> Any:
    """Create ClaudeAgentOptions with a workspace-assembled system prompt.

    The SOUL.md workspace (AGENTS.md, IDENTITY.md, USER.md, etc.) is assembled
    into the system prompt. This is *complementary* to the SDK's own
    ``setting_sources`` which handles CLAUDE.md and ``.claude/skills/``.

    Args:
        workspace_dir: Path to the workspace directory containing SOUL.md etc.
        skills_dirs: Extra directories to scan for workspace skills.
        allowed_tools: Tools the agent can use.
        permission_mode: Permission mode for the agent.
        use_preset: If True, append workspace content to Claude Code's preset.
        extra_instructions: Additional instructions to append.
        model: Model to use.
        setting_sources: SDK setting sources. Use ``["project"]`` to also load
            CLAUDE.md and ``.claude/skills/`` from the project. Default ``None``
            (SDK loads nothing from disk; only the workspace prompt is used).
        include_soul_agents: Include a soul-searcher subagent definition.
        **kwargs: Additional ClaudeAgentOptions fields.

    Returns:
        ClaudeAgentOptions if the SDK is installed, otherwise a plain dict.
    """
    assembler = SoulAssembler(
        workspace_dir=workspace_dir,
        skills_dirs=skills_dirs,
    )

    if use_preset:
        system_prompt: Any = assembler.assemble_with_preset(
            extra=extra_instructions
        )
    else:
        system_prompt = assembler.assemble()
        if extra_instructions:
            system_prompt += f"\n\n{extra_instructions}"

    agents: dict[str, Any] | None = kwargs.pop("agents", None)
    if include_soul_agents:
        agents = agents or {}
        agents.update(create_soul_search_agent())

    opts: dict[str, Any] = {
        "system_prompt": system_prompt,
        "allowed_tools": allowed_tools
        or ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        "permission_mode": permission_mode,
        "cwd": str(Path(workspace_dir).expanduser().resolve()),
    }

    if model is not None:
        opts["model"] = model

    if setting_sources is not None:
        opts["setting_sources"] = setting_sources

    if agents:
        opts["agents"] = agents

    opts.update(kwargs)

    if SDK_AVAILABLE:
        return ClaudeAgentOptions(**opts)

    return opts


def create_soul_search_agent() -> dict[str, Any]:
    """Create a subagent definition for searching workspace SOUL.md files.

    This agent is for the AI itself to use when it needs to understand the
    workspace configuration, find specific rules in SOUL.md, or check what
    skills are available.

    Returns a dict suitable for ClaudeAgentOptions.agents.
    """
    definition: dict[str, Any] = {
        "description": (
            "Search and analyze workspace SOUL.md files and skills. "
            "Use proactively when you need to understand the workspace "
            "configuration, find specific rules, check what instructions "
            "are defined in SOUL.md/AGENTS.md/TOOLS.md, or discover "
            "available skills."
        ),
        "prompt": _SOUL_SEARCH_PROMPT,
        "tools": ["Read", "Grep", "Glob"],
        "model": "haiku",
    }

    if SDK_AVAILABLE:
        return {"soul-searcher": AgentDefinition(**definition)}

    return {"soul-searcher": definition}


_SOUL_SEARCH_PROMPT = """\
You are a workspace configuration analyst. Your job is to search
and analyze the workspace bootstrap files and skills.

## Workspace bootstrap files

The workspace contains these named files that define the agent's behavior:

| File          | Purpose                                        |
|---------------|------------------------------------------------|
| AGENTS.md     | Session guidelines, memory rules, safety       |
| SOUL.md       | Agent personality, core identity, boundaries   |
| IDENTITY.md   | Name, creature type, vibe, emoji               |
| USER.md       | Human profile (name, timezone, context)        |
| TOOLS.md      | Local tool notes (cameras, SSH, voices, etc.)  |
| HEARTBEAT.md  | Periodic check tasks                           |
| BOOTSTRAP.md  | First-run onboarding (deleted after setup)     |
| MEMORY.md     | Long-term curated memory                       |

## Skills

Skills live in the `skills/` directory. Each skill has:
- `SKILL.md` with YAML frontmatter (name, description, metadata)
- Optional supporting files (scripts, templates, examples)

## Search procedure

1. Use Glob to find workspace files: `*.md`, `skills/*/SKILL.md`
2. Use Read to examine file contents
3. Use Grep to search for specific patterns across all workspace files
4. Report the workspace structure and relevant findings

Always report:
- Which bootstrap files exist and which are missing
- Key rules and instructions from each file
- Available skills with their descriptions
- Any notable configuration or customizations
"""


async def soul_query(
    prompt: str,
    workspace_dir: str | Path,
    **kwargs: Any,
) -> AsyncIterator[Any]:
    """Run a query with workspace-assembled system prompt.

    Convenience wrapper around ``claude_agent_sdk.query()``.

    Args:
        prompt: The user message to send.
        workspace_dir: Path to the SOUL.md workspace.
        **kwargs: Passed to create_soul_options().
    """
    if not SDK_AVAILABLE:
        raise RuntimeError(
            "claude-agent-sdk is not installed. "
            "Install it with: pip install claude-agent-sdk"
        )

    options = create_soul_options(workspace_dir=workspace_dir, **kwargs)
    async for message in sdk_query(prompt=prompt, options=options):
        yield message
