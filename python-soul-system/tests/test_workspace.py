"""Tests for workspace initialization and CLAUDE.md generation."""

from pathlib import Path

import pytest

from soul_system.workspace import (
    ensure_workspace,
    generate_claude_md,
    is_workspace_bootstrapped,
    refresh_claude_md,
)


class TestEnsureWorkspace:
    def test_creates_directory(self, tmp_path: Path):
        workspace = tmp_path / "new_workspace"
        result = ensure_workspace(workspace)

        assert result.exists()
        assert result.is_dir()

    def test_seeds_soul_files(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")

        assert (workspace / "SOUL.md").exists()
        assert (workspace / "AGENTS.md").exists()
        assert (workspace / "IDENTITY.md").exists()
        assert (workspace / "USER.md").exists()
        assert (workspace / "TOOLS.md").exists()

    def test_creates_claude_md_with_inlined_content(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")

        claude_md = workspace / "CLAUDE.md"
        assert claude_md.exists()

        content = claude_md.read_text()
        # File contents are inlined under ## headers
        assert "## SOUL.md" in content
        assert "## IDENTITY.md" in content
        assert "## USER.md" in content
        # Preamble declares files as user-editable
        assert "user-editable" in content

    def test_claude_md_inlines_bootstrap_when_present(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")
        content = (workspace / "CLAUDE.md").read_text()

        assert "## BOOTSTRAP.md" in content

    def test_claude_md_has_soul_persona_instruction(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")
        content = (workspace / "CLAUDE.md").read_text()

        assert "embody its persona" in content

    def test_does_not_overwrite_existing_files(self, tmp_path: Path):
        workspace = tmp_path / "ws"
        workspace.mkdir()
        (workspace / "SOUL.md").write_text("Custom soul content")

        ensure_workspace(workspace)

        assert (workspace / "SOUL.md").read_text() == "Custom soul content"

    def test_regenerates_claude_md_on_each_ensure(self, tmp_path: Path):
        workspace = tmp_path / "ws"
        workspace.mkdir()
        (workspace / "SOUL.md").write_text("Original soul")
        ensure_workspace(workspace)

        content_v1 = (workspace / "CLAUDE.md").read_text()
        assert "Original soul" in content_v1

        # Simulate an agent editing SOUL.md during a session
        (workspace / "SOUL.md").write_text("Updated soul")
        ensure_workspace(workspace)

        content_v2 = (workspace / "CLAUDE.md").read_text()
        assert "Updated soul" in content_v2
        assert "Original soul" not in content_v2

    def test_creates_claude_skills_directory(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")
        assert (workspace / ".claude" / "skills").is_dir()

    def test_creates_memory_directory(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")
        assert (workspace / "memory").is_dir()

    def test_seeds_bundled_skills(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")
        skill = workspace / ".claude" / "skills" / "soul-editor" / "SKILL.md"

        assert skill.exists()
        assert "soul files" in skill.read_text().lower()

    def test_does_not_overwrite_existing_skills(self, tmp_path: Path):
        workspace = tmp_path / "ws"
        skill_dir = workspace / ".claude" / "skills" / "soul-editor"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("Custom skill")

        ensure_workspace(workspace)

        assert (skill_dir / "SKILL.md").read_text() == "Custom skill"

    def test_skip_templates(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws", seed_templates=False)
        assert workspace.exists()
        assert not (workspace / "SOUL.md").exists()
        assert not (workspace / "CLAUDE.md").exists()


class TestGenerateClaudeMd:
    def test_inlines_file_content(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("Be helpful and kind.")
        (tmp_path / "IDENTITY.md").write_text("Name: Nova")

        content = generate_claude_md(tmp_path)

        assert "## SOUL.md" in content
        assert "Be helpful and kind." in content
        assert "## IDENTITY.md" in content
        assert "Name: Nova" in content

    def test_excludes_missing_files(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("soul content")

        content = generate_claude_md(tmp_path)

        assert "## SOUL.md" in content
        assert "## IDENTITY.md" not in content

    def test_includes_bootstrap_when_present(self, tmp_path: Path):
        (tmp_path / "BOOTSTRAP.md").write_text("onboarding steps")

        content = generate_claude_md(tmp_path)

        assert "## BOOTSTRAP.md" in content
        assert "onboarding steps" in content

    def test_excludes_bootstrap_when_absent(self, tmp_path: Path):
        content = generate_claude_md(tmp_path)
        assert "BOOTSTRAP.md" not in content

    def test_empty_workspace_has_no_project_context(self, tmp_path: Path):
        content = generate_claude_md(tmp_path)
        assert "# Project Context" not in content

    def test_has_user_editable_preamble(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("soul")

        content = generate_claude_md(tmp_path)
        assert "user-editable" in content

    def test_has_soul_persona_instruction(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("Be bold.")

        content = generate_claude_md(tmp_path)
        assert "embody its persona" in content

    def test_no_soul_instruction_without_soul_file(self, tmp_path: Path):
        (tmp_path / "USER.md").write_text("Name: Alex")

        content = generate_claude_md(tmp_path)
        assert "embody its persona" not in content


class TestRefreshClaudeMd:
    def test_regenerates_claude_md(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("soul content")
        (tmp_path / "CLAUDE.md").write_text("old content")

        refresh_claude_md(tmp_path)

        content = (tmp_path / "CLAUDE.md").read_text()
        assert "soul content" in content
        assert "old content" not in content

    def test_reflects_file_additions(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("soul")
        refresh_claude_md(tmp_path)

        assert "## IDENTITY.md" not in (tmp_path / "CLAUDE.md").read_text()

        (tmp_path / "IDENTITY.md").write_text("identity")
        refresh_claude_md(tmp_path)

        assert "## IDENTITY.md" in (tmp_path / "CLAUDE.md").read_text()
        assert "identity" in (tmp_path / "CLAUDE.md").read_text()

    def test_reflects_content_changes(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("version 1")
        refresh_claude_md(tmp_path)
        assert "version 1" in (tmp_path / "CLAUDE.md").read_text()

        (tmp_path / "SOUL.md").write_text("version 2")
        refresh_claude_md(tmp_path)
        assert "version 2" in (tmp_path / "CLAUDE.md").read_text()
        assert "version 1" not in (tmp_path / "CLAUDE.md").read_text()


class TestIsWorkspaceBootstrapped:
    def test_not_bootstrapped_with_bootstrap_file(self, tmp_path: Path):
        (tmp_path / "BOOTSTRAP.md").write_text("First run.")
        (tmp_path / "IDENTITY.md").write_text("Name: Nova")

        assert is_workspace_bootstrapped(tmp_path) is False

    def test_bootstrapped_after_bootstrap_deleted(self, tmp_path: Path):
        (tmp_path / "IDENTITY.md").write_text("Name: Nova")

        assert is_workspace_bootstrapped(tmp_path) is True

    def test_empty_workspace_not_bootstrapped(self, tmp_path: Path):
        assert is_workspace_bootstrapped(tmp_path) is False
