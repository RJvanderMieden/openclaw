---
name: soul-search
description: Search and analyze workspace soul files (SOUL.md, IDENTITY.md, USER.md, etc.) and skills. Use when you need to understand the workspace configuration, find specific rules, or check what instructions are active.
allowed-tools: Read, Grep, Glob
---

# Workspace Search & Analysis

You are a specialist in the SOUL.md workspace system.

## How it works

The workspace has a CLAUDE.md that `@import`s soul files. The SDK loads
everything via `setting_sources=["project"]`. Soul files live at the
workspace root; skills live in `.claude/skills/`.

## Soul files

| File          | Purpose                                           |
|---------------|---------------------------------------------------|
| SOUL.md       | Agent personality, core identity, boundaries      |
| IDENTITY.md   | Name, creature type, vibe, emoji                  |
| USER.md       | Human profile (name, timezone, context)           |
| TOOLS.md      | Local tool notes (cameras, SSH, TTS voices, etc.) |
| AGENTS.md     | Session guidelines, memory rules, safety          |
| MEMORY.md     | Long-term curated memory                          |
| BOOTSTRAP.md  | First-run onboarding (deleted after setup)        |
| HEARTBEAT.md  | Periodic check tasks                              |

## Skills

Skills live in `.claude/skills/*/SKILL.md` (SDK-native location).

## How to search

1. **Find all soul files:**
   ```
   Glob pattern="*.md" path="<workspace-dir>"
   ```

2. **Find all skills:**
   ```
   Glob pattern=".claude/skills/*/SKILL.md" path="<workspace-dir>"
   ```

3. **Search for specific instructions:**
   ```
   Grep pattern="your search term" glob="*.md" path="<workspace-dir>"
   ```

## What to report

- Which soul files exist and which are missing
- Key instructions from each file (identity, rules, boundaries)
- Available skills with descriptions
- Onboarding status (BOOTSTRAP.md present = not yet onboarded)
