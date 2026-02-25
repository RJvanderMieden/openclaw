"""Tests for the agent SDK integration module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from soul_system.agent import (
    SDK_AVAILABLE,
    create_soul_options,
)


@pytest.fixture
def workspace(tmp_path: Path):
    """Create a minimal workspace for agent tests."""
    (tmp_path / "SOUL.md").write_text("# Soul\n\nBe helpful and kind.")
    (tmp_path / "IDENTITY.md").write_text("# Identity\n\nName: TestBot")
    return tmp_path


class TestCreateSoulOptions:
    def test_returns_dict_when_sdk_unavailable(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(workspace_dir=workspace)

        assert isinstance(opts, dict)

    def test_default_setting_sources_is_project(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(workspace_dir=workspace)

        assert opts["setting_sources"] == ["project"]

    def test_custom_setting_sources(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(
                workspace_dir=workspace,
                setting_sources=["user", "project", "local"],
            )

        assert opts["setting_sources"] == ["user", "project", "local"]

    def test_no_system_prompt_by_default(self, workspace: Path):
        """Without extra_instructions, no system_prompt is set — SDK loads CLAUDE.md."""
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(workspace_dir=workspace)

        assert "system_prompt" not in opts

    def test_extra_instructions_as_preset_append(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(
                workspace_dir=workspace,
                extra_instructions="Focus on security.",
            )

        prompt = opts["system_prompt"]
        assert isinstance(prompt, dict)
        assert prompt["type"] == "preset"
        assert prompt["preset"] == "claude_code"
        assert "Focus on security." in prompt["append"]

    def test_default_allowed_tools(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(workspace_dir=workspace)

        assert "Read" in opts["allowed_tools"]
        assert "Grep" in opts["allowed_tools"]

    def test_custom_allowed_tools(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(
                workspace_dir=workspace,
                allowed_tools=["Read", "Glob"],
            )

        assert opts["allowed_tools"] == ["Read", "Glob"]

    def test_model_included_when_set(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(workspace_dir=workspace, model="haiku")

        assert opts["model"] == "haiku"

    def test_model_omitted_when_none(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(workspace_dir=workspace)

        assert "model" not in opts

    def test_cwd_is_resolved(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(workspace_dir=workspace)

        assert opts["cwd"] == str(workspace.resolve())

    def test_extra_kwargs_passed_through(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(workspace_dir=workspace, max_turns=5)

        assert opts["max_turns"] == 5


class TestSoulQueryErrorHandling:
    def test_raises_when_sdk_unavailable(self, workspace: Path):
        import asyncio
        from soul_system.agent import soul_query

        async def _run():
            with patch("soul_system.agent.SDK_AVAILABLE", False):
                async for _ in soul_query(
                    prompt="Hello", workspace_dir=workspace
                ):
                    pass

        with pytest.raises(RuntimeError, match="claude-agent-sdk is not installed"):
            asyncio.run(_run())
