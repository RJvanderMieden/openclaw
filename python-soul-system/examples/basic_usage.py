"""Basic usage example for the SOUL.md workspace system.

Shows how to:
1. Initialize a workspace with soul templates
2. Use the workspace with the Claude Agent SDK
3. The SDK loads CLAUDE.md (@imports soul files) + .claude/skills/ automatically

No custom assembler needed — setting_sources=["project"] does everything.
"""

import asyncio
from pathlib import Path

from soul_system.workspace import (
    ensure_workspace,
    is_workspace_bootstrapped,
    refresh_claude_md,
)
from soul_system.agent import create_soul_options, soul_query


EXAMPLE_WORKSPACE = Path(__file__).parent / "workspace"


def example_init_workspace() -> None:
    """Initialize a new workspace with soul templates."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        workspace = ensure_workspace(tmp)
        print(f"=== New Workspace at {workspace} ===")
        for f in sorted(workspace.iterdir()):
            if f.is_file():
                print(f"  {f.name} ({f.stat().st_size} bytes)")
            elif f.is_dir():
                print(f"  {f.name}/")

        print()
        print("CLAUDE.md contents:")
        print((workspace / "CLAUDE.md").read_text())

        bootstrapped = is_workspace_bootstrapped(workspace)
        print(f"Onboarding complete: {bootstrapped}")
        print("(BOOTSTRAP.md exists — agent needs to run first-run conversation)")
    print()


def example_inspect_workspace() -> None:
    """Inspect an existing workspace."""
    print(f"=== Workspace: {EXAMPLE_WORKSPACE} ===")

    # Soul files
    for f in sorted(EXAMPLE_WORKSPACE.iterdir()):
        if f.is_file():
            print(f"  {f.name} ({f.stat().st_size} bytes)")
        elif f.is_dir():
            print(f"  {f.name}/")

    # Skills
    skills_dir = EXAMPLE_WORKSPACE / ".claude" / "skills"
    if skills_dir.is_dir():
        print()
        print("Skills (.claude/skills/):")
        for skill in sorted(skills_dir.iterdir()):
            if skill.is_dir() and (skill / "SKILL.md").exists():
                print(f"  /{skill.name}")

    print()
    print("CLAUDE.md:")
    claude_md = EXAMPLE_WORKSPACE / "CLAUDE.md"
    if claude_md.exists():
        print(claude_md.read_text())
    print()


def example_sdk_options() -> None:
    """Show SDK options — setting_sources does all the work."""
    options = create_soul_options(workspace_dir=EXAMPLE_WORKSPACE)

    if isinstance(options, dict):
        print("=== SDK Options (dict, SDK not installed) ===")
        for k, v in options.items():
            print(f"  {k}: {v}")
    else:
        print("=== SDK Options (ClaudeAgentOptions) ===")
        print(f"  setting_sources: {options.setting_sources}")
        print(f"  cwd: {options.cwd}")
        print(f"  allowed_tools: {options.allowed_tools}")
    print()


async def example_query() -> None:
    """Run a query — SDK loads soul files via CLAUDE.md @import.

    NOTE: Requires ANTHROPIC_API_KEY and claude-agent-sdk.
    """
    async for message in soul_query(
        prompt="Who are you? What do you know about the user?",
        workspace_dir=EXAMPLE_WORKSPACE,
        allowed_tools=["Read", "Grep", "Glob"],
    ):
        if hasattr(message, "content"):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)


if __name__ == "__main__":
    print("--- Example: Init Workspace ---")
    example_init_workspace()

    print("--- Example: Inspect Workspace ---")
    example_inspect_workspace()

    print("--- Example: SDK Options ---")
    example_sdk_options()

    # Uncomment if you have ANTHROPIC_API_KEY set:
    # print("--- Example: Query ---")
    # asyncio.run(example_query())
