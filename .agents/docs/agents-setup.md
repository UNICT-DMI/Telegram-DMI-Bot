# Agent setup

## Layout

- `AGENTS.md`: the canonical, lean instructions. Every agent reads it, directly or through a pointer.
- `CLAUDE.md`: just `@AGENTS.md`, since Claude Code reads CLAUDE.md, not AGENTS.md. Claude-only instructions may follow the import.
- `.agents/docs/`: agent docs, each linked from AGENTS.md with a "read when…" hook, so it loads only when relevant.
- `.agents/skills/<name>/`: shared skills, each with a committed relative symlink per agent that needs one, e.g. `.claude/skills/<name>` → `../../.agents/skills/<name>`.
- `.agents/plans/`: local planning docs, gitignored.

## Adding docs and skills

- Doc: put it in `.agents/docs/` and link it from AGENTS.md as a plain markdown link with a one-line "read when…" hook. Never `@`-import it: Claude Code loads imports at startup, so the doc would always sit in context.
- Skill: put it in `.agents/skills/<name>/`, then from the repo root: `mkdir -p .claude/skills && ln -s ../../.agents/skills/<name> .claude/skills/<name>`.

## Hooking up your agent

- **Claude Code**: nothing to do; it reads CLAUDE.md and the `.claude/skills/` links.
- **Agents that read AGENTS.md natively**: nothing to do.
- **Any other agent**: point its entry file at AGENTS.md with its include mechanism, or copy AGENTS.md into it if it has none and keep the copy in sync. Link its skills dir like `.claude/skills/`. If you have the `/agentify-project` skill, it can research and wire the agent for you.

## Windows

Skills are linked with symlinks. Enable Developer Mode (or run as admin) and set `git config --global core.symlinks true` before cloning; otherwise git checks the links out as plain text files.
