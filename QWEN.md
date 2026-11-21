# QWEN.md

This file provides guidance to Qwen Code when working with code in this
repository. Qwen Code's context loader reads exactly `QWEN.md` and `AGENTS.md`
in a directory; this repo deliberately ships only `QWEN.md` — there is no
`AGENTS.md` here (each harness gets its own file; see "Prompt files by
harness" below), so this file is the sole source of project guidance for a
Qwen Code session.

## What this project is

`visualizer-cli` is the AgentCulture agent for a **web workspace for
agent-built docs and content**. Agents author structured documents with charts
and diagrams through a CLI, an HTTP API, and an MCP server, and humans view
them in the browser on desktop, phone, or remotely via a served site.

**Status: only the scaffold exists today.** It was generated from
`culture-agent-template` and contains the agent-first CLI (identity and
introspection verbs), the mesh identity, the canonical skill kit, and
CI/deploy. The document model, CLI authoring verbs, HTTP API, MCP server and
browser viewer are all **planned**. Some CLI strings (`learn`, the `explain`
root entry, the parser description) still say "a clonable template"; they are
stale.

It is a sibling to [`guildmaster`](https://github.com/agentculture/guildmaster)
(the **skills supplier**), [`steward`](https://github.com/agentculture/steward)
(**alignment** — `steward doctor`, the sibling-pattern baseline), and
[`teken`](https://github.com/agentculture/teken) (the **afi-cli** "Agent First
Interface" scaffolder this CLI is cited from) within the Organic Development
framework.

## Prompt files by harness

This repo's root carries one prompt file per agent harness, each read by
exactly one of them — there is no shared base file for them to inherit from:

- **Claude Code** → [`CLAUDE.md`](CLAUDE.md) (the fullest write-up; read it
  first if you are new to the repo).
- **Pi / associate** → [`AGENTS.override.md`](AGENTS.override.md) for context,
  plus [`.pi/SYSTEM.md`](.pi/SYSTEM.md) for its system prompt.
- **colleague** → [`AGENTS.colleague.md`](AGENTS.colleague.md).
- **Qwen Code** → this file.

## Identity

Declared in `culture.yaml`:

```yaml
agents:
- suffix: visualizer-cli
  backend: claude
```

`backend: claude` fixes the *mesh resident* prompt file to `CLAUDE.md` — the
mesh runtime reads that file, not this one. A Qwen Code session working in a
clone of this repo is a separate, local tool session; it reads `QWEN.md`
regardless of what `culture.yaml` declares, and running Qwen Code here neither
requires nor changes that declaration. The declaration and the resident prompt
together satisfy the two invariants `steward doctor` verifies:
**prompt-file-present** and **backend-consistency** (`claude` ↔ `CLAUDE.md`).

## Roadmap (planned — not built)

- One document model (prose, chart and diagram blocks) behind three thin
  fronts with the same capabilities: CLI authoring verbs, an HTTP API, and an
  MCP server.
- A responsive browser viewer for desktop and phone, servable remotely.
- [Issue #1](https://github.com/agentculture/visualizer-cli/issues/1):
  architecture diagrams rendered as interactive React Flow graphs (pan/zoom,
  phone-friendly, standalone HTML), with Mermaid kept as source/fallback. The
  first target is the `embodiment` layer diagram. Open questions (React Flow
  package choice, how the JS ships, and the missing source diagram) are
  tracked in `CLAUDE.md`.

## The CLI

The CLI is cited (cite-don't-import) from teken's `python-cli` reference
(`teken cli cite`), so the runtime package has **no third-party dependencies**;
`teken` (a.k.a. `afi-cli`) is a dev dependency only. The console script is
`visualizer` (e.g. `uv run visualizer whoami`); `visualizer-cli` is the
program/dist name used below. Agent-first verbs:

- `visualizer-cli whoami` — identity from `culture.yaml`.
- `visualizer-cli learn` — structured self-teaching prompt.
- `visualizer-cli explain <path>` — markdown docs for any noun/verb.
- `visualizer-cli overview` — descriptive snapshot of the agent.
- `visualizer-cli doctor` — check the agent-identity invariants.
- `visualizer-cli cli overview` — describe the CLI surface itself.

Conventions: every command supports `--json`; results go to stdout, errors and
diagnostics to stderr (never mixed); exit codes are `0` success, `1` user
error, `2` environment error, `3+` reserved. The agent-first rubric is
enforced in CI by `teken cli doctor . --strict`.

## Skills

`.claude/skills/` vendors the **canonical guildmaster skill kit**
(cite-don't-import). Provenance and the re-sync procedure live in
`docs/skill-sources.md`. Do not reformat or edit vendored scripts — re-sync
from guildmaster instead.

## Conventions

- **Every PR bumps the version** — even docs/config/CI. Use the
  `version-bump` skill; the `version-check` CI job blocks merge otherwise.
- **Tests**: `uv run pytest -n auto`. **Lint**: black, isort, flake8 (line
  length 100), bandit, markdownlint.
- **File length limit**: no tracked source file may exceed **400 lines**.
  The cap and checked extensions live in `pyproject.toml`
  `[tool.file-length]` (`max-lines`; `file-types` = `.py`, `.js`, `.jsx`,
  `.ts`, `.tsx`) and CI enforces it with
  `python3 scripts/check-file-length.py`. Vendored skills are exempt. Split
  files into modules (see `scripts/_harness_smoke/`).
- **Deploy**: pushing to `main` publishes to PyPI via Trusted Publishing
  (`.github/workflows/publish.yml`); PRs do a TestPyPI dry-run.

## Layout

```text
visualizer_cli/   agent-first CLI (cited from teken's python-cli reference)
  cli/                    parser, error/output contract, _commands/ (verbs)
  explain/                markdown catalog for `explain`
tests/                    pytest smoke + introspection tests
scripts/                  CI gates: scan-secrets, check-file-length, harness-smoke (+ _harness_smoke/)
.claude/skills/           vendored guildmaster skill kit (cite-don't-import)
docs/skill-sources.md     skill provenance ledger
culture.yaml              mesh identity (suffix + backend)
.github/workflows/        tests + deploy (PyPI Trusted Publishing)
```

This file describes the repository **as it exists on disk today**. When you
edit, keep claims grounded in checked-in reality; if a section drifts ahead of
reality, mark it `(planned)` or move it under a `## Roadmap` heading. For the
full set of workflow conventions (worktree layout, memory discipline,
`ask-colleague` usage), see [`CLAUDE.md`](CLAUDE.md) — those conventions apply
to work in this repo regardless of which harness is doing it.
