"""Claude Agent SDK integration for the SOUL.md workspace system.

Provides helper functions to create SDK options with workspace-assembled
system prompts, and programmatic subagent definitions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncIterator

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    query,
)
from claude_agent_sdk.types import AgentDefinition

from soul_system.assembler import SoulAssembler


def create_soul_options(
    workspace_dir: str | Path,
    *,
    skills_dirs: list[str | Path] | None = None,
    allowed_tools: list[str] | None = None,
    permission_mode: str = "acceptEdits",
    use_preset: bool = False,
    extra_instructions: str | None = None,
    model: str | None = None,
    include_soul_agents: bool = False,
    **kwargs: Any,
) -> ClaudeAgentOptions:
    """Create ClaudeAgentOptions with a workspace-assembled system prompt.

    Args:
        workspace_dir: Path to the workspace directory containing SOUL.md etc.
        skills_dirs: Extra directories to scan for skills.
        allowed_tools: Tools the agent can use.
        permission_mode: Permission mode for the agent.
        use_preset: If True, append workspace content to Claude Code's preset prompt.
        extra_instructions: Additional instructions to append.
        model: Model to use.
        include_soul_agents: Include the soul-searcher subagent definition.
        **kwargs: Additional ClaudeAgentOptions fields.
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

    agents = kwargs.pop("agents", None) or {}
    if include_soul_agents:
        agents.update(create_soul_search_agent())

    return ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=allowed_tools
        or ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        permission_mode=permission_mode,
        cwd=str(Path(workspace_dir).expanduser().resolve()),
        model=model,
        agents=agents if agents else None,
        **kwargs,
    )


def create_soul_search_agent() -> dict[str, AgentDefinition]:
    """Create a subagent that can search through SOUL.md and workspace files.

    This agent is for the AI itself to use when it needs to understand the
    workspace configuration, find specific rules in SOUL.md, or check what
    skills are available.

    Returns a dict suitable for ClaudeAgentOptions.agents.
    """
    return {
        "soul-searcher": AgentDefinition(
            description=(
                "Search and analyze workspace SOUL.md files and skills. "
                "Use proactively when you need to understand the workspace "
                "configuration, find specific rules, check what instructions "
                "are defined in SOUL.md/AGENTS.md/TOOLS.md, or discover "
                "available skills."
            ),
            prompt="""You are a workspace configuration analyst. Your job is to search
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
""",
            tools=["Read", "Grep", "Glob"],
            model="haiku",
        )
    }


async def soul_query(
    prompt: str,
    workspace_dir: str | Path,
    **kwargs: Any,
) -> AsyncIterator[Any]:
    """Run a query with workspace-assembled system prompt.

    Convenience wrapper around claude_agent_sdk.query().
    """
    options = create_soul_options(workspace_dir=workspace_dir, **kwargs)
    async for message in query(prompt=prompt, options=options):
        yield message


async def soul_client(
    workspace_dir: str | Path,
    *,
    include_soul_agents: bool = True,
    **kwargs: Any,
) -> ClaudeSDKClient:
    """Create a ClaudeSDKClient with workspace-assembled system prompt.

    Returns a client ready for multi-turn conversation.
    """
    options = create_soul_options(
        workspace_dir=workspace_dir,
        include_soul_agents=include_soul_agents,
        **kwargs,
    )
    return ClaudeSDKClient(options=options)
