"""Workspace bootstrap file loading and truncation.

Mirrors OpenClaw's workspace.ts and pi-embedded-helpers/bootstrap.ts:
- Load named workspace files (AGENTS.md, SOUL.md, TOOLS.md, etc.)
- Truncate large files with smart head/tail split (70% head, 20% tail)
- Enforce total character budget across all files
"""

from __future__ import annotations

from pathlib import Path

from soul_system.types import (
    BOOTSTRAP_FILENAMES,
    HEAD_RATIO,
    TAIL_RATIO,
    BootstrapContext,
    BootstrapFile,
    WorkspaceConfig,
)


def load_bootstrap_files(config: WorkspaceConfig) -> list[BootstrapFile]:
    """Load all workspace bootstrap files.

    Looks for AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md,
    HEARTBEAT.md, BOOTSTRAP.md, and MEMORY.md in the workspace directory.
    Also loads any extra bootstrap files specified in config.
    """
    files: list[BootstrapFile] = []
    workspace = config.workspace_dir

    for name in BOOTSTRAP_FILENAMES:
        file_path = workspace / name
        if file_path.is_file():
            content = file_path.read_text(encoding="utf-8")
            files.append(BootstrapFile(name=name, path=file_path, content=content))
        else:
            files.append(BootstrapFile(name=name, path=file_path, missing=True))

    # Extra bootstrap files (custom workspace additions)
    for extra in config.extra_bootstrap_files:
        extra_path = workspace / extra
        if extra_path.is_file():
            content = extra_path.read_text(encoding="utf-8")
            files.append(
                BootstrapFile(name=extra, path=extra_path, content=content)
            )

    return files


def strip_frontmatter(content: str) -> str:
    """Strip YAML frontmatter from the beginning of a file.

    Mirrors OpenClaw's stripFrontMatter() in workspace.ts.
    """
    if not content.startswith("---"):
        return content
    end_index = content.find("\n---", 3)
    if end_index == -1:
        return content
    return content[end_index + 4 :].lstrip()


def truncate_content(
    content: str,
    file_name: str,
    max_chars: int,
) -> tuple[str, bool]:
    """Truncate content with smart head/tail split.

    Keeps 70% from the start, 20% from the end, with a truncation marker
    in between. Mirrors OpenClaw's trimBootstrapContent().

    Returns (content, was_truncated).
    """
    trimmed = content.rstrip()
    if len(trimmed) <= max_chars:
        return trimmed, False

    head_chars = int(max_chars * HEAD_RATIO)
    tail_chars = int(max_chars * TAIL_RATIO)
    head = trimmed[:head_chars]
    tail = trimmed[-tail_chars:] if tail_chars > 0 else ""

    marker = (
        f"\n[...truncated, read {file_name} for full content...]\n"
        f"...(truncated {file_name}: kept {head_chars}+{tail_chars} chars of {len(trimmed)})...\n"
    )

    return head + marker + tail, True


def build_bootstrap_context(
    files: list[BootstrapFile],
    config: WorkspaceConfig,
) -> list[BootstrapContext]:
    """Build the bootstrap context from loaded files.

    Applies per-file and total character limits, strips frontmatter,
    and truncates oversized files. Mirrors OpenClaw's
    buildBootstrapContextFiles().
    """
    remaining = config.total_max_chars
    result: list[BootstrapContext] = []

    for file in files:
        if remaining <= 0:
            break

        if file.missing:
            missing_text = f"[MISSING] Expected at: {file.path}"
            if len(missing_text) > remaining:
                break
            remaining -= len(missing_text)
            result.append(
                BootstrapContext(
                    path=str(file.path),
                    content=missing_text,
                    original_length=0,
                )
            )
            continue

        if file.content is None:
            continue

        # Strip frontmatter before injecting
        clean_content = strip_frontmatter(file.content)

        # Apply per-file limit, capped by remaining budget
        file_max = min(config.max_chars_per_file, remaining)
        truncated_content, was_truncated = truncate_content(
            clean_content, file.name, file_max
        )

        # Final clamp to remaining budget
        if len(truncated_content) > remaining:
            truncated_content = truncated_content[:remaining]
            was_truncated = True

        remaining -= len(truncated_content)
        result.append(
            BootstrapContext(
                path=str(file.path),
                content=truncated_content,
                truncated=was_truncated,
                original_length=len(clean_content),
            )
        )

    return result
