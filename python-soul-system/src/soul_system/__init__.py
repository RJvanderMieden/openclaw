"""SOUL.md workspace system prompt assembler for the Claude Agent SDK.

This package assembles agent personality, identity, and memory from a set of
named workspace files (SOUL.md, AGENTS.md, IDENTITY.md, USER.md, TOOLS.md, etc.)
into a system prompt that can be passed to the Claude Agent SDK.

How this relates to the SDK's built-in features
------------------------------------------------

The Claude Agent SDK already handles CLAUDE.md and .claude/skills/ loading
when you set ``setting_sources=["project"]``. That covers **project coding
instructions** and **Claude Code skills**.

This package handles a different layer: **agent personality and memory** via
the SOUL.md workspace concept (inspired by OpenClaw). The two are complementary:

- CLAUDE.md (SDK-managed): Project coding conventions, tool configs, rules
- SOUL.md workspace (this package): Agent identity, personality, user profile,
  memory, tools, session guidelines

Usage::

    from soul_system import SoulAssembler

    # Assemble workspace into a system prompt
    assembler = SoulAssembler(workspace_dir="~/.my-agent/workspace")
    system_prompt = assembler.assemble()

    # Use with Claude Agent SDK
    from claude_agent_sdk import query, ClaudeAgentOptions
    async for msg in query(
        prompt="Hello",
        options=ClaudeAgentOptions(
            system_prompt=system_prompt,
            # Also load CLAUDE.md and .claude/skills/ from the project:
            setting_sources=["project"],
        ),
    ):
        print(msg)

    # Or use the convenience helper:
    from soul_system.agent import create_soul_options
    options = create_soul_options(
        workspace_dir="~/.my-agent/workspace",
        setting_sources=["project"],  # also load CLAUDE.md
    )
"""

from soul_system.assembler import SoulAssembler
from soul_system.types import (
    BootstrapContext,
    BootstrapFile,
    SkillEntry,
    WorkspaceConfig,
)

__all__ = [
    "SoulAssembler",
    "BootstrapFile",
    "BootstrapContext",
    "SkillEntry",
    "WorkspaceConfig",
]
