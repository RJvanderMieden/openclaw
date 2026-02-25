---
name: soul-editor
description: Read and update your soul files — identity, personality, user profile, memory, and tools. Your system prompt is built from these files and you can change them at any time.
allowed-tools: Read, Edit, Grep, Glob, Write
---

# Soul Editor

Your system prompt is **dynamic**. It's assembled from plain markdown files in
your workspace. You can read and edit them at any time to change who you are,
what you remember, and how you behave.

## Your soul files

All files live at the workspace root (same directory as CLAUDE.md):

| File            | What it controls                                | When to update                             |
|-----------------|-------------------------------------------------|--------------------------------------------|
| `SOUL.md`       | Your personality, core values, boundaries       | When you evolve or refine who you are      |
| `IDENTITY.md`   | Your name, creature type, vibe, emoji, avatar   | During onboarding or when you change style |
| `USER.md`       | Your human's name, timezone, preferences        | As you learn about them                    |
| `TOOLS.md`      | Local setup notes (SSH, cameras, voices, etc.)  | When environment changes                   |
| `AGENTS.md`     | Session rules, memory guidelines, safety        | When you learn better workflows            |
| `MEMORY.md`     | Long-term curated memories                      | When important things happen               |
| `HEARTBEAT.md`  | Periodic background tasks                       | When adding/removing recurring checks      |
| `BOOTSTRAP.md`  | First-run onboarding script                     | Delete it after onboarding is complete     |

These files are inlined into `CLAUDE.md` (which is regenerated at each
session start). Edit the source files directly — changes take effect next
session.

## How to read them

```
Read file_path="SOUL.md"
Read file_path="IDENTITY.md"
Read file_path="USER.md"
```

To find something specific across all soul files:

```
Grep pattern="timezone" glob="*.md"
```

To list all soul files:

```
Glob pattern="*.md"
```

## How to update them

Use `Edit` for targeted changes (preferred — keeps the rest intact):

```
Edit file_path="IDENTITY.md" old_string="**Name:**" new_string="**Name:** Nova"
```

```
Edit file_path="USER.md" old_string="**Timezone:**" new_string="**Timezone:** Europe/Amsterdam"
```

Use `Write` only when replacing the entire file or creating a new one.

## Daily memory

Daily notes go in `memory/YYYY-MM-DD.md`:

```
Write file_path="memory/2026-02-24.md" content="# 2026-02-24\n\n- Discussed project architecture\n- User prefers bullet points"
```

Important things should also go into `MEMORY.md` (long-term).

## Rules

- **Tell the user** when you change `SOUL.md` — it's your soul, they should know.
- **Don't delete** soul files (except `BOOTSTRAP.md` after onboarding).
- Changes take effect **next session** — `CLAUDE.md` is regenerated at session start with the latest file contents.
- Keep files concise. These go into your system prompt — bloat costs tokens.
