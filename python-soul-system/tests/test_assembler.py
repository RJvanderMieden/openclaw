"""Tests for the SoulAssembler."""

from pathlib import Path

import pytest

from soul_system.assembler import SoulAssembler


@pytest.fixture
def workspace(tmp_path: Path):
    """Create a complete workspace."""
    (tmp_path / "AGENTS.md").write_text("# Agents\n\nSession guidelines here.")
    (tmp_path / "SOUL.md").write_text("# Soul\n\nBe genuinely helpful.")
    (tmp_path / "IDENTITY.md").write_text("# Identity\n\nName: Nova")
    (tmp_path / "USER.md").write_text("# User\n\nName: Alex")
    (tmp_path / "TOOLS.md").write_text("# Tools\n\nSSH: dev-server")
    (tmp_path / "MEMORY.md").write_text("# Memory\n\nProject uses FastAPI.")

    # Add a skill
    skill_dir = tmp_path / "skills" / "hello"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: hello\ndescription: Greet the user\n---\n\nSay hello warmly."
    )

    return tmp_path


class TestSoulAssembler:
    def test_assemble_produces_string(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        prompt = assembler.assemble()

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_includes_bootstrap_content(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        prompt = assembler.assemble()

        assert "Be genuinely helpful" in prompt
        assert "Session guidelines" in prompt
        assert "Name: Nova" in prompt

    def test_includes_skills(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        prompt = assembler.assemble()

        assert "hello" in prompt
        assert "Greet the user" in prompt

    def test_separates_sections(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        prompt = assembler.assemble()

        # Sections are separated by ---
        assert "---" in prompt

    def test_get_file_summary(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        assembler.load()
        summary = assembler.get_file_summary()

        assert "SOUL.md" in summary
        assert "AGENTS.md" in summary
        assert "hello" in summary
        assert str(workspace) in summary

    def test_get_bootstrap_files(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        files = assembler.get_bootstrap_files()

        names = [f.name for f in files]
        assert "SOUL.md" in names
        assert "AGENTS.md" in names

    def test_get_context_files(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        contexts = assembler.get_context_files()

        assert len(contexts) > 0
        assert any("Be genuinely helpful" in c.content for c in contexts)

    def test_get_skills(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        skills = assembler.get_skills()

        assert len(skills) == 1
        assert skills[0].name == "hello"

    def test_assemble_for_sdk_plain(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        result = assembler.assemble_for_sdk()

        assert isinstance(result, str)
        assert "Be genuinely helpful" in result

    def test_assemble_for_sdk_with_append(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        result = assembler.assemble_for_sdk(append="Extra instructions.")

        assert isinstance(result, str)
        assert "Extra instructions." in result

    def test_assemble_with_preset(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        result = assembler.assemble_with_preset(extra="Focus on security.")

        assert isinstance(result, dict)
        assert result["type"] == "preset"
        assert result["preset"] == "claude_code"
        assert "Be genuinely helpful" in result["append"]
        assert "Focus on security." in result["append"]

    def test_auto_loads_on_assemble(self, workspace: Path):
        assembler = SoulAssembler(workspace_dir=workspace)
        # Don't call load() manually — assemble() should auto-load
        prompt = assembler.assemble()
        assert "Be genuinely helpful" in prompt


class TestSoulAssemblerEdgeCases:
    def test_empty_workspace(self, tmp_path: Path):
        assembler = SoulAssembler(workspace_dir=tmp_path)
        prompt = assembler.assemble()

        # Should still produce something (MISSING markers)
        assert "[MISSING]" in prompt

    def test_workspace_with_frontmatter(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text(
            "---\ntitle: My Soul\nsummary: Agent soul\n---\n\n# Soul\n\nBe good."
        )
        assembler = SoulAssembler(workspace_dir=tmp_path)
        prompt = assembler.assemble()

        # Frontmatter should be stripped
        assert "title: My Soul" not in prompt
        assert "Be good" in prompt

    def test_extra_skills_dirs(self, tmp_path: Path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "SOUL.md").write_text("# Soul")

        extra = tmp_path / "extra"
        skill = extra / "weather"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: weather\ndescription: Check weather\n---\nWeather info."
        )

        assembler = SoulAssembler(
            workspace_dir=workspace,
            skills_dirs=[extra],
        )
        prompt = assembler.assemble()
        assert "weather" in prompt

    def test_custom_budgets(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("x" * 50_000)
        assembler = SoulAssembler(
            workspace_dir=tmp_path,
            max_chars_per_file=1000,
            total_max_chars=2000,
        )
        prompt = assembler.assemble()
        assert len(prompt) <= 3000  # some overhead for headers/separators
