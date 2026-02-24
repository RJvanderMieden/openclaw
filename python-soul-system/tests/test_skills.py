"""Tests for skill discovery and prompt formatting."""

from pathlib import Path

import pytest

from soul_system.skills import discover_skills, format_skills_for_prompt
from soul_system.types import WorkspaceConfig


@pytest.fixture
def workspace_with_skills(tmp_path: Path):
    """Create a workspace with skill directories."""
    # Skill 1: github
    github = tmp_path / "skills" / "github"
    github.mkdir(parents=True)
    (github / "SKILL.md").write_text(
        "---\nname: github\ndescription: GitHub operations via gh CLI\n---\n\n"
        "# GitHub Skill\n\nUse `gh` commands for GitHub operations."
    )

    # Skill 2: slack (user-invocable: false)
    slack = tmp_path / "skills" / "slack"
    slack.mkdir(parents=True)
    (slack / "SKILL.md").write_text(
        "---\nname: slack\ndescription: Slack messaging\nuser-invocable: false\n---\n\n"
        "# Slack Skill\n\nBackground Slack integration."
    )

    # Skill 3: deploy (disable-model-invocation: true)
    deploy = tmp_path / "skills" / "deploy"
    deploy.mkdir(parents=True)
    (deploy / "SKILL.md").write_text(
        "---\nname: deploy\ndescription: Deploy to production\n"
        "disable-model-invocation: true\n---\n\n"
        "# Deploy Skill\n\nManual deployment workflow."
    )

    return tmp_path


class TestDiscoverSkills:
    def test_discovers_skills_in_workspace(self, workspace_with_skills: Path):
        config = WorkspaceConfig(workspace_dir=workspace_with_skills)
        skills = discover_skills(config)

        names = [s.name for s in skills]
        assert "github" in names
        assert "slack" in names
        assert "deploy" in names

    def test_parses_frontmatter(self, workspace_with_skills: Path):
        config = WorkspaceConfig(workspace_dir=workspace_with_skills)
        skills = discover_skills(config)

        github = next(s for s in skills if s.name == "github")
        assert github.description == "GitHub operations via gh CLI"
        assert github.user_invocable is True
        assert github.disable_model_invocation is False

    def test_parses_invocation_policy(self, workspace_with_skills: Path):
        config = WorkspaceConfig(workspace_dir=workspace_with_skills)
        skills = discover_skills(config)

        slack = next(s for s in skills if s.name == "slack")
        assert slack.user_invocable is False

        deploy = next(s for s in skills if s.name == "deploy")
        assert deploy.disable_model_invocation is True

    def test_discovers_from_extra_dirs(self, workspace_with_skills: Path, tmp_path: Path):
        extra = tmp_path / "extra_skills"
        weather = extra / "weather"
        weather.mkdir(parents=True)
        (weather / "SKILL.md").write_text(
            "---\nname: weather\ndescription: Check the weather\n---\n\nWeather info."
        )

        config = WorkspaceConfig(
            workspace_dir=workspace_with_skills,
            skills_dirs=[extra],
        )
        skills = discover_skills(config)

        names = [s.name for s in skills]
        assert "weather" in names
        assert "github" in names

    def test_workspace_overrides_extra(self, workspace_with_skills: Path, tmp_path: Path):
        """Workspace skills should override extra skills with the same name."""
        extra = tmp_path / "extra_skills"
        github_extra = extra / "github"
        github_extra.mkdir(parents=True)
        (github_extra / "SKILL.md").write_text(
            "---\nname: github\ndescription: OLD github\n---\n\nOld version."
        )

        config = WorkspaceConfig(
            workspace_dir=workspace_with_skills,
            skills_dirs=[extra],
        )
        skills = discover_skills(config)

        github = next(s for s in skills if s.name == "github")
        assert github.description == "GitHub operations via gh CLI"  # workspace version wins

    def test_empty_skills_dir(self, tmp_path: Path):
        config = WorkspaceConfig(workspace_dir=tmp_path)
        skills = discover_skills(config)
        assert skills == []

    def test_skips_hidden_directories(self, tmp_path: Path):
        hidden = tmp_path / "skills" / ".hidden"
        hidden.mkdir(parents=True)
        (hidden / "SKILL.md").write_text("---\nname: hidden\n---\nHidden skill.")

        config = WorkspaceConfig(workspace_dir=tmp_path)
        skills = discover_skills(config)
        assert len(skills) == 0

    def test_skips_directories_without_skill_md(self, tmp_path: Path):
        no_skill = tmp_path / "skills" / "not-a-skill"
        no_skill.mkdir(parents=True)
        (no_skill / "README.md").write_text("Not a skill.")

        config = WorkspaceConfig(workspace_dir=tmp_path)
        skills = discover_skills(config)
        assert len(skills) == 0


class TestFormatSkillsForPrompt:
    def test_formats_visible_skills(self, workspace_with_skills: Path):
        config = WorkspaceConfig(workspace_dir=workspace_with_skills)
        skills = discover_skills(config)
        prompt = format_skills_for_prompt(skills, config)

        # github and slack should be visible (not disable-model-invocation)
        assert "github" in prompt
        assert "slack" in prompt
        # deploy has disable-model-invocation: true, should be excluded
        assert "deploy" not in prompt

    def test_empty_skills_produces_empty_prompt(self, tmp_path: Path):
        config = WorkspaceConfig(workspace_dir=tmp_path)
        prompt = format_skills_for_prompt([], config)
        assert prompt == ""

    def test_respects_count_limit(self, workspace_with_skills: Path):
        config = WorkspaceConfig(
            workspace_dir=workspace_with_skills,
            max_skills_in_prompt=1,
        )
        skills = discover_skills(config)
        prompt = format_skills_for_prompt(skills, config)

        # Should only include 1 skill (github or slack, not both)
        lines = [l for l in prompt.splitlines() if l.startswith("## ")]
        assert len(lines) == 1
