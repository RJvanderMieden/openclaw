"""Claude Agent SDK integration for the SOUL.md workspace system.

Since the workspace uses CLAUDE.md with ``@import`` directives, the SDK loads
all soul files automatically when ``setting_sources=["project"]`` is set.
No custom assembler needed — the SDK does everything.

Usage::

    from soul_system.agent import create_soul_options

    # The SDK loads CLAUDE.md (which @imports SOUL.md, IDENTITY.md, etc.)
    options = create_soul_options(workspace_dir="~/.my-agent/workspace")

    from claude_agent_sdk import query
    async for msg in query(prompt="Hello", options=options):
        print(msg)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncIterator

# SDK imports are deferred so tests can run without the SDK installed.
try:
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        query as sdk_query,
    )

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


def create_soul_options(
    workspace_dir: str | Path,
    *,
    allowed_tools: list[str] | None = None,
    permission_mode: str = "acceptEdits",
    model: str | None = None,
    setting_sources: list[str] | None = None,
    extra_instructions: str | None = None,
    **kwargs: Any,
) -> Any:
    """Create ClaudeAgentOptions for a soul workspace.

    The SDK loads CLAUDE.md (which ``@import``s the soul files) automatically
    via ``setting_sources``. Default is ``["project"]``.

    Args:
        workspace_dir: Path to the workspace containing CLAUDE.md + soul files.
        allowed_tools: Tools the agent can use.
        permission_mode: Permission mode for the agent.
        model: Model to use.
        setting_sources: SDK setting sources. Default ``["project"]`` which
            loads CLAUDE.md, .claude/settings.json, and .claude/skills/.
        extra_instructions: Additional system prompt text to append.
        **kwargs: Additional ClaudeAgentOptions fields.

    Returns:
        ClaudeAgentOptions if the SDK is installed, otherwise a plain dict.
    """
    resolved = Path(workspace_dir).expanduser().resolve()

    # Default to ["project"] so the SDK loads CLAUDE.md and .claude/skills/
    if setting_sources is None:
        setting_sources = ["project"]

    opts: dict[str, Any] = {
        "setting_sources": setting_sources,
        "allowed_tools": allowed_tools
        or ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        "permission_mode": permission_mode,
        "cwd": str(resolved),
    }

    if model is not None:
        opts["model"] = model

    # Extra instructions go into system_prompt (appended to what SDK loads)
    if extra_instructions:
        opts["system_prompt"] = {
            "type": "preset",
            "preset": "claude_code",
            "append": extra_instructions,
        }

    opts.update(kwargs)

    if SDK_AVAILABLE:
        return ClaudeAgentOptions(**opts)

    return opts


async def soul_query(
    prompt: str,
    workspace_dir: str | Path,
    **kwargs: Any,
) -> AsyncIterator[Any]:
    """Run a query against a soul workspace.

    The SDK loads CLAUDE.md (with @imported soul files) and .claude/skills/
    automatically.

    Args:
        prompt: The user message to send.
        workspace_dir: Path to the workspace.
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
