"""Tests for workspace bootstrap file loading and truncation."""

from pathlib import Path

import pytest

from soul_system.bootstrap import (
    build_bootstrap_context,
    load_bootstrap_files,
    strip_frontmatter,
    truncate_content,
)
from soul_system.types import BootstrapFile, WorkspaceConfig


@pytest.fixture
def workspace(tmp_path: Path):
    """Create a workspace with bootstrap files."""
    (tmp_path / "AGENTS.md").write_text("# Agents\n\nSession guidelines.")
    (tmp_path / "SOUL.md").write_text("# Soul\n\nBe helpful.")
    (tmp_path / "TOOLS.md").write_text("# Tools\n\nSSH: dev-server")
    (tmp_path / "IDENTITY.md").write_text("# Identity\n\nName: Nova")
    (tmp_path / "USER.md").write_text("# User\n\nName: Alex")
    return tmp_path


class TestLoadBootstrapFiles:
    def test_loads_existing_files(self, workspace: Path):
        config = WorkspaceConfig(workspace_dir=workspace)
        files = load_bootstrap_files(config)

        names = [f.name for f in files if not f.missing]
        assert "AGENTS.md" in names
        assert "SOUL.md" in names
        assert "TOOLS.md" in names

    def test_marks_missing_files(self, workspace: Path):
        config = WorkspaceConfig(workspace_dir=workspace)
        files = load_bootstrap_files(config)

        missing = [f for f in files if f.missing]
        missing_names = [f.name for f in missing]
        assert "HEARTBEAT.md" in missing_names
        assert "BOOTSTRAP.md" in missing_names

    def test_loads_content(self, workspace: Path):
        config = WorkspaceConfig(workspace_dir=workspace)
        files = load_bootstrap_files(config)

        soul = next(f for f in files if f.name == "SOUL.md")
        assert soul.content is not None
        assert "Be helpful" in soul.content

    def test_loads_extra_files(self, workspace: Path):
        (workspace / "CUSTOM.md").write_text("Custom content")
        config = WorkspaceConfig(
            workspace_dir=workspace,
            extra_bootstrap_files=["CUSTOM.md"],
        )
        files = load_bootstrap_files(config)

        custom = next((f for f in files if f.name == "CUSTOM.md"), None)
        assert custom is not None
        assert custom.content == "Custom content"

    def test_empty_workspace(self, tmp_path: Path):
        config = WorkspaceConfig(workspace_dir=tmp_path)
        files = load_bootstrap_files(config)

        assert all(f.missing for f in files)


class TestStripFrontmatter:
    def test_strips_yaml_frontmatter(self):
        content = "---\ntitle: Test\n---\n\n# Hello"
        assert strip_frontmatter(content) == "# Hello"

    def test_preserves_content_without_frontmatter(self):
        content = "# Hello\n\nWorld"
        assert strip_frontmatter(content) == content

    def test_handles_incomplete_frontmatter(self):
        content = "---\ntitle: Test\nno closing"
        assert strip_frontmatter(content) == content


class TestTruncateContent:
    def test_no_truncation_when_within_limit(self):
        content = "Short content"
        result, truncated = truncate_content(content, "test.md", 100)
        assert result == content
        assert truncated is False

    def test_truncates_large_content(self):
        content = "x" * 1000
        result, truncated = truncate_content(content, "test.md", 100)
        assert truncated is True
        assert len(result) < 1000
        assert "truncated" in result

    def test_keeps_head_and_tail(self):
        content = "HEAD" + "x" * 1000 + "TAIL"
        result, truncated = truncate_content(content, "test.md", 200)
        assert truncated is True
        assert result.startswith("HEAD")
        assert result.endswith("TAIL")


class TestBuildBootstrapContext:
    def test_builds_context_from_files(self, workspace: Path):
        config = WorkspaceConfig(workspace_dir=workspace)
        files = load_bootstrap_files(config)
        context = build_bootstrap_context(files, config)

        contents = [c.content for c in context]
        assert any("Be helpful" in c for c in contents)

    def test_respects_total_budget(self, workspace: Path):
        # Write a large file
        (workspace / "AGENTS.md").write_text("x" * 100_000)
        config = WorkspaceConfig(
            workspace_dir=workspace, total_max_chars=1000
        )
        files = load_bootstrap_files(config)
        context = build_bootstrap_context(files, config)

        total = sum(len(c.content) for c in context)
        assert total <= 1000

    def test_marks_truncated_files(self, workspace: Path):
        (workspace / "AGENTS.md").write_text("x" * 50_000)
        config = WorkspaceConfig(
            workspace_dir=workspace, max_chars_per_file=1000
        )
        files = load_bootstrap_files(config)
        context = build_bootstrap_context(files, config)

        agents = next(c for c in context if "AGENTS" in c.path)
        assert agents.truncated is True

    def test_strips_frontmatter(self, workspace: Path):
        (workspace / "SOUL.md").write_text(
            "---\ntitle: Test\n---\n\n# Soul Content"
        )
        config = WorkspaceConfig(workspace_dir=workspace)
        files = load_bootstrap_files(config)
        context = build_bootstrap_context(files, config)

        soul = next(c for c in context if "SOUL" in c.path)
        assert "---" not in soul.content
        assert "# Soul Content" in soul.content

    def test_includes_missing_marker(self, workspace: Path):
        config = WorkspaceConfig(workspace_dir=workspace)
        files = load_bootstrap_files(config)
        context = build_bootstrap_context(files, config)

        missing_contexts = [c for c in context if "[MISSING]" in c.content]
        assert len(missing_contexts) > 0
