---
name: soul-search
description: Search and analyze workspace bootstrap files (SOUL.md, AGENTS.md, TOOLS.md, etc.) and skills. Use when you need to understand the workspace configuration, find specific rules, check what instructions are active, or debug system prompt assembly.
allowed-tools: Read, Grep, Glob
---

# Workspace Search & Analysis

You are a specialist in the SOUL.md workspace system.

## Workspace bootstrap files

The workspace contains named files that define the agent's behavior. These files
are loaded at session start and assembled into the system prompt:

| File          | Purpose                                           |
|---------------|---------------------------------------------------|
| AGENTS.md     | Session guidelines, memory rules, safety          |
| SOUL.md       | Agent personality, core identity, boundaries      |
| IDENTITY.md   | Name, creature type, vibe, emoji                  |
| USER.md       | Human profile (name, timezone, context)           |
| TOOLS.md      | Local tool notes (cameras, SSH, TTS voices, etc.) |
| HEARTBEAT.md  | Periodic check tasks                              |
| BOOTSTRAP.md  | First-run onboarding (deleted after setup)        |
| MEMORY.md     | Long-term curated memory                          |

## Skills

Skills live in `skills/*/SKILL.md`. Each SKILL.md has:
- YAML frontmatter: `name`, `description`, `allowed-tools`, `user-invocable`, `disable-model-invocation`
- Markdown content with instructions for the agent
- Optional supporting files (scripts, templates, examples)

## How to search

1. **Find all workspace files:**
   ```
   Glob pattern="*.md" path="<workspace-dir>"
   ```

2. **Find all skills:**
   ```
   Glob pattern="skills/*/SKILL.md" path="<workspace-dir>"
   ```

3. **Search for specific instructions:**
   ```
   Grep pattern="your search term" glob="*.md" path="<workspace-dir>"
   Grep pattern="your search term" glob="skills/*/SKILL.md" path="<workspace-dir>"
   ```

4. **Check what the agent's personality is:**
   ```
   Read file_path="<workspace-dir>/SOUL.md"
   ```

## What to report

When analyzing the workspace, always report:
- **Which bootstrap files exist** and which are missing
- **Key instructions** from each file (identity, rules, boundaries)
- **Available skills** with their descriptions
- **Memory state** (daily notes, long-term memory entries)
- **Onboarding status** (BOOTSTRAP.md present = not yet onboarded)

## Python API

```python
from soul_system import SoulAssembler

assembler = SoulAssembler(workspace_dir="~/.my-agent/workspace")
assembler.load()

# Inspect loaded files
print(assembler.get_file_summary())

# Get the assembled system prompt
prompt = assembler.assemble()
```
