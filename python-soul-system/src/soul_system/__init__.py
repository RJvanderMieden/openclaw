"""SOUL.md system prompt assembler for Claude Agent SDK.

Mirrors OpenClaw's workspace bootstrap system: a set of named template files
(SOUL.md, AGENTS.md, IDENTITY.md, USER.md, TOOLS.md, MEMORY.md, etc.) that
are discovered in a workspace directory, truncated to fit token budgets, and
assembled into context files for the system prompt.

Skills (SKILL.md) are separate: they live in a skills/ directory and get
formatted into the prompt so the agent knows what capabilities it has.

Usage:
    from soul_system import SoulAssembler

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

from soul_system.assembler import SoulAssembler
from soul_system.types import (
    BootstrapFile,
    BootstrapContext,
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
