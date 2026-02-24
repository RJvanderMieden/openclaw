"""Tests for workspace initialization."""

from pathlib import Path

import pytest

from soul_system.workspace import ensure_workspace, is_workspace_bootstrapped


class TestEnsureWorkspace:
    def test_creates_directory(self, tmp_path: Path):
        workspace = tmp_path / "new_workspace"
        result = ensure_workspace(workspace)

        assert result.exists()
        assert result.is_dir()

    def test_seeds_template_files(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")

        assert (workspace / "SOUL.md").exists()
        assert (workspace / "AGENTS.md").exists()
        assert (workspace / "IDENTITY.md").exists()
        assert (workspace / "USER.md").exists()
        assert (workspace / "TOOLS.md").exists()

    def test_does_not_overwrite_existing(self, tmp_path: Path):
        workspace = tmp_path / "ws"
        workspace.mkdir()
        (workspace / "SOUL.md").write_text("Custom soul content")

        ensure_workspace(workspace)

        assert (workspace / "SOUL.md").read_text() == "Custom soul content"

    def test_creates_skills_directory(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")
        assert (workspace / "skills").is_dir()

    def test_creates_memory_directory(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws")
        assert (workspace / "memory").is_dir()

    def test_skip_templates(self, tmp_path: Path):
        workspace = ensure_workspace(tmp_path / "ws", seed_templates=False)
        # Directory should exist but no template files
        assert workspace.exists()
        assert not (workspace / "SOUL.md").exists()


class TestIsWorkspaceBootstrapped:
    def test_not_bootstrapped_with_bootstrap_file(self, tmp_path: Path):
        (tmp_path / "BOOTSTRAP.md").write_text("First run.")
        (tmp_path / "IDENTITY.md").write_text("Name: Nova")

        assert is_workspace_bootstrapped(tmp_path) is False

    def test_bootstrapped_after_bootstrap_deleted(self, tmp_path: Path):
        (tmp_path / "IDENTITY.md").write_text("Name: Nova")
        # BOOTSTRAP.md doesn't exist → onboarding is done

        assert is_workspace_bootstrapped(tmp_path) is True

    def test_empty_workspace_not_bootstrapped(self, tmp_path: Path):
        assert is_workspace_bootstrapped(tmp_path) is False
