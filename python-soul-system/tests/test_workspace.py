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

    def test_creates_claude_md(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")

        claude_md = workspace / "CLAUDE.md"
        assert claude_md.exists()

        content = claude_md.read_text()
        assert "@import SOUL.md" in content
        assert "@import IDENTITY.md" in content
        assert "@import USER.md" in content

    def test_claude_md_includes_bootstrap_when_present(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")
        content = (workspace / "CLAUDE.md").read_text()

        assert "@import BOOTSTRAP.md" in content

    def test_does_not_overwrite_existing_files(self, tmp_path: Path):
        workspace = tmp_path / "ws"
        workspace.mkdir()
        (workspace / "SOUL.md").write_text("Custom soul content")

        ensure_workspace(workspace)

        assert (workspace / "SOUL.md").read_text() == "Custom soul content"

    def test_does_not_overwrite_existing_claude_md(self, tmp_path: Path):
        workspace = tmp_path / "ws"
        workspace.mkdir()
        (workspace / "CLAUDE.md").write_text("# My custom CLAUDE.md")

        ensure_workspace(workspace)

        assert (workspace / "CLAUDE.md").read_text() == "# My custom CLAUDE.md"

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
    def test_includes_existing_files(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("soul")
        (tmp_path / "IDENTITY.md").write_text("identity")

        content = generate_claude_md(tmp_path)

        assert "@import SOUL.md" in content
        assert "@import IDENTITY.md" in content

    def test_excludes_missing_files(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("soul")

        content = generate_claude_md(tmp_path)

        assert "@import SOUL.md" in content
        assert "@import IDENTITY.md" not in content

    def test_includes_bootstrap_when_present(self, tmp_path: Path):
        (tmp_path / "BOOTSTRAP.md").write_text("onboarding")

        content = generate_claude_md(tmp_path)
        assert "@import BOOTSTRAP.md" in content

    def test_excludes_bootstrap_when_absent(self, tmp_path: Path):
        content = generate_claude_md(tmp_path)
        assert "BOOTSTRAP.md" not in content

    def test_empty_workspace_has_no_import_directives(self, tmp_path: Path):
        content = generate_claude_md(tmp_path)
        # No @import <file> lines (header comment mentioning @imports is fine)
        lines = content.splitlines()
        import_lines = [l for l in lines if l.startswith("@import ")]
        assert len(import_lines) == 0


class TestRefreshClaudeMd:
    def test_regenerates_claude_md(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("soul")
        (tmp_path / "CLAUDE.md").write_text("old content")

        refresh_claude_md(tmp_path)

        content = (tmp_path / "CLAUDE.md").read_text()
        assert "@import SOUL.md" in content
        assert "old content" not in content

    def test_reflects_file_additions(self, tmp_path: Path):
        (tmp_path / "SOUL.md").write_text("soul")
        refresh_claude_md(tmp_path)

        assert "@import IDENTITY.md" not in (tmp_path / "CLAUDE.md").read_text()

        (tmp_path / "IDENTITY.md").write_text("identity")
        refresh_claude_md(tmp_path)

        assert "@import IDENTITY.md" in (tmp_path / "CLAUDE.md").read_text()


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
