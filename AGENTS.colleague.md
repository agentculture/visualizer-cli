# Colleague Resident — `visualizer-cli`

You are a colleague session working in a clone of this template — reading
this file because colleague's prompt cascade resolves it here, not because
`culture.yaml` selected you. That declaration says `backend: claude`, so
`CLAUDE.md` is this template's *mesh resident* prompt; colleague remains fully
usable interactively over the same clone, and this file is what it loads when
you run it. A clone that declares `backend: colleague` promotes this file to
its resident prompt as well — the guidance below holds either way.

Your job is to assist with scoped tasks delegated by the operator or peer
agents, using the colleague tool-loop (`read_file` / `write_file` /
`edit_file` / `list_dir` / `run_command` / `finish`).

## The prompt cascade (and what this repo actually ships)

colleague concatenates up to three files, in order, as its prompt cascade:

1. `AGENTS.md` — a shared base, if present.
2. `AGENTS.colleague.md` — this file.
3. `AGENTS.colleague.<sanitized-model>.md` — a model-specific override, if
   present.

**This repo ships only layer 2.** There is deliberately no `AGENTS.md` at the
root (a shared base across the four harness files was proposed and rejected —
each harness gets its own, unrelated file; see `CLAUDE.md`'s "Prompt files by
harness"), so the cascade for colleague in this repo starts and ends at this
file. There is also no `AGENTS.colleague.<sanitized-model>.md` — this repo
doesn't need per-model overrides today. If you add one of those files later,
update this section so the docs keep matching what's actually on disk.

## What this project is

`visualizer-cli` is the AgentCulture agent for a web workspace for
agent-built docs and content. Agents author structured documents with charts
and diagrams through a CLI, an HTTP API, and an MCP server, and humans view
them in the browser. **Today only the scaffold exists**: the agent-first CLI
(identity/introspection verbs), the mesh identity, the skill kit, and CI. The
document model, the fronts and the viewer are planned, as is
[issue #1](https://github.com/agentculture/visualizer-cli/issues/1)
(interactive React Flow diagrams exported as standalone HTML, with Mermaid as
source/fallback).

`CLAUDE.md` is written for a Claude Code session, so it is not your runtime
prompt. It is still the fullest write-up of the repo's conventions and
architecture (CLI contract, roadmap, open questions on issue #1). Read it when
you need more context than fits here.

## How you work

- Prefer small, reversible steps; hand off via `finish` when done.
- Follow the operator's instructions and any skills loaded from
  `.colleague/skills/` when present.
- The vendored skills under `.claude/skills/` are cited **verbatim** from
  guildmaster — don't reformat or edit their scripts; a fix belongs upstream
  (see `docs/skill-sources.md` for the re-sync procedure).
- Every PR bumps the version (`version-bump` skill) — CI's `version-check` job
  blocks merge otherwise.
- No tracked source file (`.py`, `.js`, `.jsx`, `.ts`, `.tsx`) may exceed
  **400 lines**. The cap and extensions are set in `pyproject.toml`
  `[tool.file-length]` (`max-lines`, `file-types`) and checked by
  `python3 scripts/check-file-length.py` in CI. Split a file that grows too
  large into modules (see `scripts/_harness_smoke/`).
- Run tests with `uv run pytest -n auto`. The console script is `visualizer`
  (for example `uv run visualizer whoami`), not `visualizer-cli`.
