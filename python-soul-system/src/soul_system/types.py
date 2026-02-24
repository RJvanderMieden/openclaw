"""Type definitions for the SOUL.md system prompt assembler."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# The canonical set of workspace bootstrap filenames, mirroring OpenClaw's workspace.ts
BOOTSTRAP_FILENAMES: list[str] = [
    "AGENTS.md",
    "SOUL.md",
    "TOOLS.md",
    "IDENTITY.md",
    "USER.md",
    "HEARTBEAT.md",
    "BOOTSTRAP.md",
    "MEMORY.md",
]

# Default truncation limits (mirrors OpenClaw's pi-embedded-helpers/bootstrap.ts)
DEFAULT_MAX_CHARS_PER_FILE = 20_000
DEFAULT_TOTAL_MAX_CHARS = 150_000

# Truncation ratios: keep 70% from the start, 20% from the end
HEAD_RATIO = 0.7
TAIL_RATIO = 0.2

# Skill loading limits (mirrors OpenClaw's skills/workspace.ts)
DEFAULT_MAX_SKILLS_IN_PROMPT = 150
DEFAULT_MAX_SKILLS_PROMPT_CHARS = 30_000
DEFAULT_MAX_SKILL_FILE_BYTES = 256_000


@dataclass
class BootstrapFile:
    """A single workspace bootstrap file (SOUL.md, AGENTS.md, etc.)."""

    name: str
    path: Path
    content: str | None = None
    missing: bool = False


@dataclass
class BootstrapContext:
    """A processed bootstrap file ready for system prompt injection."""

    path: str
    content: str
    truncated: bool = False
    original_length: int = 0


@dataclass
class SkillEntry:
    """A discovered skill with its metadata."""

    name: str
    description: str
    file_path: Path
    base_dir: Path
    content: str
    frontmatter: dict = field(default_factory=dict)
    user_invocable: bool = True
    disable_model_invocation: bool = False


@dataclass
class WorkspaceConfig:
    """Configuration for the workspace assembler."""

    workspace_dir: Path
    skills_dirs: list[Path] = field(default_factory=list)
    max_chars_per_file: int = DEFAULT_MAX_CHARS_PER_FILE
    total_max_chars: int = DEFAULT_TOTAL_MAX_CHARS
    max_skills_in_prompt: int = DEFAULT_MAX_SKILLS_IN_PROMPT
    max_skills_prompt_chars: int = DEFAULT_MAX_SKILLS_PROMPT_CHARS
    max_skill_file_bytes: int = DEFAULT_MAX_SKILL_FILE_BYTES
    extra_bootstrap_files: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.workspace_dir = Path(self.workspace_dir).expanduser().resolve()
        self.skills_dirs = [Path(d).expanduser().resolve() for d in self.skills_dirs]
