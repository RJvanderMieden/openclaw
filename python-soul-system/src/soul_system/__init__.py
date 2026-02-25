"""SOUL.md workspace system for the Claude Agent SDK.

Creates a workspace with soul files (SOUL.md, IDENTITY.md, USER.md, etc.)
and a CLAUDE.md that ``@import``s them. The SDK loads everything automatically
via ``setting_sources=["project"]``.

No custom assembler needed — the SDK handles file loading, skills, and
system prompt assembly natively.

Usage::

    from soul_system.workspace import ensure_workspace
    from soul_system.agent import create_soul_options, soul_query

    # 1. Create a workspace with soul templates
    workspace = ensure_workspace("~/.my-agent/workspace")

    # 2. Use with the Claude Agent SDK
    options = create_soul_options(workspace_dir=workspace)

    from claude_agent_sdk import query
    async for msg in query(prompt="Hello", options=options):
        print(msg)
"""

from soul_system.types import WorkspaceConfig

__all__ = [
    "WorkspaceConfig",
]
