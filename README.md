# visualizer-cli

Web workspace for agent-built docs and content: agents author structured documents with charts and diagrams through a CLI, an HTTP API front, and an MCP server, and humans view them in the browser on desktop, phone, or remotely via a served site.

> **Status: early scaffold.** What exists today is the agent-first CLI
> skeleton (identity and introspection verbs), the mesh identity, the vendored
> skill kit, and CI/deploy. The document workspace itself is
> [planned](#roadmap).

## Quickstart

```bash
uv sync
uv run pytest -n auto              # run the test suite
uv run visualizer whoami           # identity from culture.yaml
uv run visualizer learn --json     # self-teaching prompt for agents
uv run teken cli doctor . --strict # the agent-first rubric gate CI runs
```

The installed console script is `visualizer`. The program and package are
named `visualizer-cli`, and `python -m visualizer_cli` also works.

## CLI

| Verb | What it does |
|------|--------------|
| `whoami` | Report this agent's nick, version, backend, and model from `culture.yaml`. |
| `learn` | Print a structured self-teaching prompt. |
| `explain <path>` | Markdown docs for any noun/verb path. |
| `overview` | Read-only descriptive snapshot of the agent. |
| `doctor` | Check the agent-identity invariants (prompt-file-present, backend-consistency). |
| `cli overview` | Describe the CLI surface itself. |

Every command supports `--json`. Results go to stdout, errors/diagnostics to
stderr (never mixed). Exit codes: `0` success, `1` user error, `2` environment
error, `3+` reserved. The CLI is cited from
[teken](https://github.com/agentculture/teken) (`afi-cli`) and the runtime
package has no third-party dependencies.

## Roadmap

Planned. None of the items below is built yet.

- **Document model**: structured documents made of prose, chart, and diagram
  blocks.
- **Three agent fronts over one model**: CLI authoring verbs, an HTTP API, and
  an MCP server, all with the same capabilities.
- **Browser viewer**: responsive on desktop and phone, and servable remotely.
- **Interactive diagrams**
  ([#1](https://github.com/agentculture/visualizer-cli/issues/1)): render
  architecture diagrams as pan/zoom React Flow graphs, exported as standalone
  HTML, with Mermaid kept as the source and fallback. The first target is the
  `embodiment` layer diagram (Surface → embodiment daemon → lobes gateway
  roles → eidetic/coherence memory).

## Development

| Check | Command |
|-------|---------|
| Tests | `uv run pytest -n auto` (coverage floor 60%) |
| Format / lint | `uv run black --check visualizer_cli tests`, `uv run isort --check-only visualizer_cli tests`, `uv run flake8 visualizer_cli tests` |
| Security | `uv run bandit -c pyproject.toml -r visualizer_cli`, `python3 scripts/scan-secrets.py` |
| File length | `python3 scripts/check-file-length.py` (400-line cap) |
| Markdown | `markdownlint-cli2 "**/*.md"` |
| Harness configs | `uv run python scripts/harness-smoke.py --stage all --require config` |

**File length limit.** No tracked source file may exceed **400 lines**.
`pyproject.toml` `[tool.file-length]` sets the cap (`max-lines = 400`) and the
checked extensions (`file-types`: `.py`, plus `.js`/`.jsx`/`.ts`/`.tsx` for the
planned frontend). The CI lint job enforces it. The
vendored skills are exempt. Long files are split into modules instead of
exempted: `scripts/_harness_smoke/` is the example.

**Every PR bumps the version**, including docs- or CI-only PRs; the
`version-check` job blocks merge otherwise. A push to `main` that touches the
package publishes to PyPI through Trusted Publishing, and PRs publish a
TestPyPI dev build.

## Prompt files by harness

Four harnesses, four root files, no shared base. Each file is read by exactly
one harness:

| Harness | File(s) |
|---------|---------|
| Claude Code | [`CLAUDE.md`](CLAUDE.md) (the fullest write-up; read it first) |
| Pi / associate | [`AGENTS.override.md`](AGENTS.override.md) + [`.pi/SYSTEM.md`](.pi/SYSTEM.md) |
| colleague | [`AGENTS.colleague.md`](AGENTS.colleague.md) |
| Qwen Code | [`QWEN.md`](QWEN.md) |

There is intentionally **no `AGENTS.md`** at the root. It would shadow the Pi
and colleague files, and CI fails if one appears. All four harnesses can be
used interactively at the same time.

`culture.yaml`'s `backend` (`claude`) selects only the **mesh resident**, the
agent the Culture daemon starts and the one `steward doctor` checks. It does
not limit which harness you can run in this clone. See
[`docs/harness-selection.md`](docs/harness-selection.md) and
[`docs/automation-contract.md`](docs/automation-contract.md).

## Skills

`.claude/skills/` vendors the guildmaster skill kit verbatim
(cite-don't-import). `.qwen/skills`, `.colleague/skills` and `.pi/skills` are
symlinks onto it. Provenance and the re-sync procedure are in
[`docs/skill-sources.md`](docs/skill-sources.md).

## The `gate` section

`culture.yaml` carries a top-level `gate` section that declares how to set up
and test this repo, so tooling (for example a PR-fixer that re-runs checks
before pushing) needs no per-repo knowledge:

```yaml
gate:
  setup:
  - [uv, sync]
  test:
  - [uv, run, pytest, -n, auto]
```

Each command is an argv list (never a shell string), and commands run in order
from the repo root. Culture's loader ignores unknown top-level keys.

## License

Apache 2.0. See [`LICENSE`](LICENSE).
