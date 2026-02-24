"""Basic usage example for the SOUL.md workspace system.

This example shows how to:
1. Initialize a workspace with template files
2. Load and inspect workspace bootstrap files
3. Discover skills
4. Assemble the full system prompt
5. Use the assembled prompt with the Claude Agent SDK
6. Combine with setting_sources to also load CLAUDE.md

The SOUL.md workspace is *complementary* to the SDK's built-in
``setting_sources`` which handles CLAUDE.md and ``.claude/skills/``.
"""

import asyncio
from pathlib import Path

from soul_system.assembler import SoulAssembler
from soul_system.workspace import ensure_workspace, is_workspace_bootstrapped
from soul_system.agent import create_soul_options, soul_query


EXAMPLE_WORKSPACE = Path(__file__).parent / "workspace"


def example_inspect_workspace() -> None:
    """Load and inspect a workspace's bootstrap files and skills."""
    assembler = SoulAssembler(workspace_dir=EXAMPLE_WORKSPACE)
    assembler.load()

    print("=== Workspace Summary ===")
    print(assembler.get_file_summary())
    print()


def example_assemble_prompt() -> None:
    """Assemble the full system prompt from workspace files."""
    assembler = SoulAssembler(workspace_dir=EXAMPLE_WORKSPACE)
    prompt = assembler.assemble()

    print("=== Assembled System Prompt ===")
    print(f"Total length: {len(prompt)} chars")
    print()
    # Show first 1000 chars
    print(prompt[:1000])
    if len(prompt) > 1000:
        print(f"... ({len(prompt) - 1000} more chars)")
    print()


def example_init_workspace() -> None:
    """Initialize a new workspace with template files."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        workspace = ensure_workspace(tmp)
        print(f"=== New Workspace at {workspace} ===")
        for f in sorted(workspace.iterdir()):
            if f.is_file():
                print(f"  {f.name} ({f.stat().st_size} bytes)")
            elif f.is_dir():
                print(f"  {f.name}/")

        # Check onboarding status
        bootstrapped = is_workspace_bootstrapped(workspace)
        print(f"\nOnboarding complete: {bootstrapped}")
        print("(BOOTSTRAP.md exists — agent needs to run first-run conversation)")
    print()


def example_sdk_options() -> None:
    """Show how to create SDK options with workspace prompt.

    Demonstrates the two complementary layers:
    - SOUL.md workspace: Agent personality, identity, memory (this package)
    - CLAUDE.md / .claude/skills/: Project coding instructions (SDK built-in)
    """
    # Mode 1: Custom system prompt (workspace only)
    options = create_soul_options(
        workspace_dir=EXAMPLE_WORKSPACE,
        allowed_tools=["Read", "Grep", "Glob"],
    )
    prompt = options.system_prompt if hasattr(options, "system_prompt") else options["system_prompt"]
    print("=== SDK Options (workspace only) ===")
    print(f"System prompt length: {len(prompt)} chars")
    print()

    # Mode 2: Workspace + CLAUDE.md loading via setting_sources
    # setting_sources=["project"] tells the SDK to also load CLAUDE.md
    # and .claude/skills/ from the project directory.
    options_with_sources = create_soul_options(
        workspace_dir=EXAMPLE_WORKSPACE,
        setting_sources=["project"],
        allowed_tools=["Read", "Grep", "Glob"],
    )
    print("=== SDK Options (workspace + setting_sources) ===")
    ss = options_with_sources.setting_sources if hasattr(options_with_sources, "setting_sources") else options_with_sources.get("setting_sources")
    print(f"setting_sources: {ss}")
    print("(SDK will also load CLAUDE.md and .claude/skills/ from disk)")
    print()

    # Mode 3: Preset mode (extends Claude Code's built-in prompt)
    options_preset = create_soul_options(
        workspace_dir=EXAMPLE_WORKSPACE,
        use_preset=True,
        extra_instructions="Focus on Python best practices.",
        setting_sources=["project"],
    )
    print("=== SDK Options (preset mode) ===")
    preset = options_preset.system_prompt if hasattr(options_preset, "system_prompt") else options_preset["system_prompt"]
    print(f"System prompt type: {type(preset).__name__}")
    if isinstance(preset, dict):
        print(f"Preset: {preset.get('preset')}")
        print(f"Append length: {len(preset.get('append', ''))} chars")
    print()


async def example_query() -> None:
    """Run a query using the workspace-assembled system prompt.

    NOTE: Requires ANTHROPIC_API_KEY to be set and claude-agent-sdk installed.
    """
    async for message in soul_query(
        prompt="Who are you? What do you know about the user you're helping?",
        workspace_dir=EXAMPLE_WORKSPACE,
        allowed_tools=["Read", "Grep", "Glob"],
        permission_mode="acceptEdits",
        # Also load CLAUDE.md if present in the project:
        setting_sources=["project"],
    ):
        if hasattr(message, "content"):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)


if __name__ == "__main__":
    print("--- Example: Inspect Workspace ---")
    example_inspect_workspace()

    print("--- Example: Assemble Prompt ---")
    example_assemble_prompt()

    print("--- Example: Init Workspace ---")
    example_init_workspace()

    print("--- Example: SDK Options ---")
    example_sdk_options()

    # Uncomment if you have ANTHROPIC_API_KEY set:
    # print("--- Example: Query ---")
    # asyncio.run(example_query())
