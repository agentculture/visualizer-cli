# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is — and where it actually stands

`visualizer-cli` is the AgentCulture mesh agent for a **web workspace for
agent-built docs and content**: agents author structured documents with charts
and diagrams through a CLI, an HTTP API front, and an MCP server; humans view
them in the browser on desktop, phone, or remotely via a served site.

**Today the repo is only the scaffold** it was generated from
(`culture-agent-template`): an agent-first CLI with identity/introspection verbs,
the mesh identity, the vendored skill kit, and CI/deploy. None of the product
surfaces exist yet — no document model, no renderer, no HTTP API, no MCP server,
no web viewer. Several strings still describe the package as "a clonable
template" (`_build_parser()` description in `visualizer_cli/cli/__init__.py`,
`_ROOT` in `visualizer_cli/explain/catalog.py`, the `learn` text). Treat those
as stale and update them when you touch the CLI surface. When you document
something, mark unbuilt things `(planned)` — keep docs matched to what is on
disk.

## Commands

```bash
uv sync                                    # install runtime + dev group
uv run pytest -n auto                      # full suite (what culture.yaml's gate runs)
uv run pytest tests/test_cli.py::test_whoami_json -v   # a single test
uv run pytest -n auto --cov=visualizer_cli --cov-report=term   # coverage (fail_under = 60)
uv run visualizer whoami                   # run the CLI
```

The console script is **`visualizer`** (`[project.scripts]`); argparse's
`prog`, the dist name and every doc string say `visualizer-cli`. So
`uv run visualizer-cli …` does **not** work; use `uv run visualizer …` or
`uv run python -m visualizer_cli …`.

The lint job in `.github/workflows/tests.yml` runs all of these, and they all
have to pass:

```bash
python3 scripts/scan-secrets.py            # committed secrets / non-localhost endpoints
python3 scripts/check-file-length.py       # 400-line gate (see below)
uv run black --check visualizer_cli tests
uv run isort --check-only visualizer_cli tests
uv run flake8 visualizer_cli tests         # line length 100, E203/W503 ignored
uv run bandit -c pyproject.toml -r visualizer_cli
markdownlint-cli2 "**/*.md" "#node_modules" "#.local" "#.claude/skills" "#.teken"
uv run teken cli doctor . --strict         # agent-first rubric gate
uv run python scripts/harness-smoke.py --stage all --require config   # harness-smoke job
```

### File length limit (400 lines)

No tracked source file may exceed **400 lines**. `pyproject.toml`
`[tool.file-length]` sets both the cap (`max-lines`) and which extensions count
(`file-types`, currently `.py` plus the planned frontend's
`.js`/`.jsx`/`.ts`/`.tsx`). Change them there, not in code. CI's lint job runs
`python3 scripts/check-file-length.py`, which checks `git ls-files` output, so
a new file is not checked until you `git add` it. You can also pass paths
(`… check-file-length.py path.py`) or override with `--max N`. The vendored
`.claude/skills/` are exempt. The gate is cited from `culture-agent-template`
(this repo's base) along with the harness-smoke split. When a file approaches
the cap, split it into focused modules. The worked examples are
`scripts/_harness_smoke/` (one module per stage behind the thin
`scripts/harness-smoke.py`) and `tests/smoke_support.py` + `tests/conftest.py`.

## CLI architecture (the contract new verbs must follow)

The CLI is **cited** (cite-don't-import) from teken's `python-cli` reference,
so the runtime package has **zero third-party dependencies**
(`dependencies = []`); `teken`, `pyyaml` and the test/lint tools are dev-only.
Adding a runtime dependency (for example a web framework for the HTTP API) is a
deliberate decision. Call it out in the PR.

- **Registration**: `visualizer_cli/cli/__init__.py::_build_parser()` imports
  each module under `cli/_commands/` and calls its `register(sub)`. A new verb
  or noun group is a new module with a `register()` that sets
  `func=<handler>`; then add one line in `_build_parser()`.
- **Error contract**: handlers return `None`/`int` or raise
  `cli/_errors.py::CliError(code, message, remediation)`. `_dispatch()` turns
  any other exception into a `CliError`, so a traceback never reaches stderr.
  Argparse errors use the same path through `_CliArgumentParser.error()`.
  `main()` checks raw argv for `--json` before parsing so that parse errors
  can also be rendered as JSON.
- **Output contract**: every verb supports `--json`. Results go to stdout
  through `cli/_output.py::emit_result`, errors to stderr through `emit_error`,
  and the two are never mixed. Exit codes: `0` ok, `1` user error, `2`
  environment error, `3+` reserved.
- **Self-description must track the surface**: a new verb also needs an entry
  in `visualizer_cli/explain/catalog.py` (keyed by command-path tuple), a line
  in the `learn` output and in the catalog's root verb list. `teken cli doctor
  . --strict` grades this agent-first rubric, including descriptive verbs that
  must not hard-fail on a bad path (`tests/test_cli_introspection.py`).
- **Identity**: `whoami`/`doctor` find this package's *own* `culture.yaml`
  by walking up from the module (`whoami.py::find_culture_yaml`). From a wheel
  install there is none, and they degrade to an info result.
  `doctor`'s backend→prompt-file tables mirror
  `.claude/skills/agent-config/data/backend-fingerprints.yaml`, and
  `tests/test_harness_registries.py` fails if the two drift apart.

## Product roadmap (planned — nothing below is built)

The description commits to five surfaces over one shared document model:
**document model** (structured docs with chart and diagram blocks) → **CLI
authoring verbs** → **HTTP API** → **MCP server** → **browser viewer**,
responsive for desktop and phone and servable remotely. Keep the model and
rendering in the package, and keep the CLI, HTTP and MCP layers as thin fronts
over it so that all three stay feature-equivalent.

### Issue #1 — React Flow diagrams (open requirement)

[agentculture/visualizer-cli#1](https://github.com/agentculture/visualizer-cli/issues/1),
filed by the `embodiment` agent, asks for architecture diagrams to render as
**interactive React Flow diagrams** instead of static images or raw Mermaid:

1. First target: the embodiment stack, Surface (agentfront) → embodiment
   daemon → lobes gateway roles → eidetic/coherence memory.
2. A node for each layer and module, and edges for the data flows
   (transcript, memory, TTS, SSE).
3. Pan/zoom, usable on phone and in the browser, emitted as **standalone
   HTML**.
4. Mermaid remains the fallback and the source of the diagram. React Flow is
   the primary visual, so the design needs a path from Mermaid source to a
   React Flow graph.

Points still open on this issue:

- The issue names `@reactflow/core`. That is the v11 package; React Flow
  v12+ ships as `@xyflow/react`. Choose deliberately and pin an exact version.
- "Standalone HTML" plus zero runtime Python dependencies means the JS has to
  be either vendored or bundled into package data, or loaded from a pinned CDN.
  That trade-off has not been decided yet.
- The reference is the sibling checkout's `../embodiment/report.md`
  (**read-only**; never modify the embodiment repo). As of 2026-11-21 that file is a 48-line Q&A
  report with **no** "Architecture (layers + loop)" Mermaid block. Ask the
  embodiment agent, or comment on the issue, for the actual source diagram
  before building against it.

## Prompt files by harness (four files, deliberately no `AGENTS.md`)

| Harness | File(s) |
|---------|---------|
| Claude Code | `CLAUDE.md` (this file; also the **mesh resident** prompt because `culture.yaml` says `backend: claude`) |
| Pi / associate | `AGENTS.override.md` (context) + `.pi/SYSTEM.md` (read-only system prompt) |
| colleague | `AGENTS.colleague.md` |
| Qwen Code | `QWEN.md` |

- **Never create a root `AGENTS.md`.** It would shadow `AGENTS.override.md` in
  Pi's loader and slot in ahead of `AGENTS.colleague.md` in colleague's
  cascade, and the `harness-smoke` CI job (`no-bare-agents-md`) fails on it.
- When repo facts change (what the project is, commands, conventions), update
  `AGENTS.colleague.md`, `AGENTS.override.md` and `QWEN.md` along with this
  file. `.pi/SYSTEM.md` contains identity only and rarely changes.
- `culture.yaml`'s `backend` selects only the mesh resident. Every harness can
  still be used interactively (`docs/harness-selection.md`,
  `docs/automation-contract.md`).
- `culture.yaml`'s `gate` section (`setup`/`test` argv lists) is how external
  tooling sets up and tests this repo. Keep it in sync with the real commands.

## Skills

`.claude/skills/` is the guildmaster skill kit, **vendored verbatim**. Never
edit or reformat these files; fixes go upstream and are then re-synced. See
`docs/skill-sources.md` for provenance and the re-sync procedure. Each
vendored `SKILL.md` must carry `type: command`, or culture's loader silently
skips it. `.qwen/skills`, `.colleague/skills` and `.pi/skills` are relative
symlinks onto `.claude/skills` (tested by `tests/test_qwen_skills_symlink.py`
and others). Skills used most often here: `cicd` (PR lane, needs `devex` on
PATH), `version-bump`, `run-tests`, `ask-colleague` (independent second
opinion on a diff), and `communicate` (cross-repo issues / mesh messages,
needs `agtag`).

## Workflow conventions

- **Every PR bumps the version**, docs/CI-only PRs included.
  `python3 .claude/skills/version-bump/scripts/bump.py patch|minor|major`
  (changelog JSON on stdin) updates `pyproject.toml` and prepends a
  Keep-a-Changelog entry to `CHANGELOG.md`. The `version-check` job blocks
  merge if the version matches `main`. `__version__` comes from package
  metadata, so do not hand-edit it.
- **Deploy**: a push to `main` that touches `pyproject.toml` or
  `visualizer_cli/**` publishes to PyPI through Trusted Publishing
  (`.github/workflows/publish.yml`). Same-repo PRs publish a
  `<version>.devN` build to TestPyPI.
- **SonarCloud** runs in the test job only when `SONAR_TOKEN` is set, and a
  red quality gate fails CI (`sonar.qualitygate.wait=true`). Coverage paths
  must stay repo-relative (`relative_files = true`).
- Branch off `main` before committing. Use the `cicd` skill to open PRs and
  handle review threads; it signs posts automatically as
  `- visualizer-cli (Claude)`.
