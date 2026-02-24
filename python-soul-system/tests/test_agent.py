"""Tests for the agent SDK integration module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from soul_system.agent import (
    SDK_AVAILABLE,
    create_soul_options,
    create_soul_search_agent,
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
        assert "system_prompt" in opts
        assert "Be helpful" in opts["system_prompt"]

    def test_includes_setting_sources(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(
                workspace_dir=workspace,
                setting_sources=["project"],
            )

        assert opts["setting_sources"] == ["project"]

    def test_omits_setting_sources_when_none(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(workspace_dir=workspace)

        assert "setting_sources" not in opts

    def test_preset_mode(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(
                workspace_dir=workspace,
                use_preset=True,
                extra_instructions="Extra.",
            )

        prompt = opts["system_prompt"]
        assert isinstance(prompt, dict)
        assert prompt["type"] == "preset"
        assert prompt["preset"] == "claude_code"
        assert "Be helpful" in prompt["append"]
        assert "Extra." in prompt["append"]

    def test_custom_mode_with_extra_instructions(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(
                workspace_dir=workspace,
                extra_instructions="Also be concise.",
            )

        assert "Also be concise." in opts["system_prompt"]

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
            opts = create_soul_options(
                workspace_dir=workspace, model="haiku"
            )

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
            opts = create_soul_options(
                workspace_dir=workspace, max_turns=5
            )

        assert opts["max_turns"] == 5


class TestCreateSoulSearchAgent:
    def test_returns_dict_with_soul_searcher(self):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            agents = create_soul_search_agent()

        assert "soul-searcher" in agents

    def test_agent_has_required_fields(self):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            agents = create_soul_search_agent()
            agent = agents["soul-searcher"]

        assert "description" in agent
        assert "prompt" in agent
        assert "tools" in agent
        assert "model" in agent
        assert agent["model"] == "haiku"
        assert "Read" in agent["tools"]
        assert "Grep" in agent["tools"]
        assert "Glob" in agent["tools"]

    def test_include_soul_agents_in_options(self, workspace: Path):
        with patch("soul_system.agent.SDK_AVAILABLE", False):
            opts = create_soul_options(
                workspace_dir=workspace,
                include_soul_agents=True,
            )

        assert "agents" in opts
        assert "soul-searcher" in opts["agents"]


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
