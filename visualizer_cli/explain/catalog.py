"""Markdown catalog for ``visualizer-cli explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty tuple
and ``("visualizer-cli",)`` both resolve to the root entry.

Keep bodies self-contained: an agent reading one entry should get enough
context without chaining reads.
"""

from __future__ import annotations

_ROOT = """\
# visualizer-cli

A clonable template for AgentCulture mesh agents. It carries an agent-first CLI
(cited from the teken `python-cli` reference), a mesh identity (`culture.yaml` +
`CLAUDE.md`), the canonical guildmaster skill kit under `.claude/skills/`, and a
buildable/deployable package baseline. Clone it, rename the package, edit
`culture.yaml`, and you have a new agent.

## Verbs

- `visualizer-cli whoami` — identity probe from `culture.yaml`.
- `visualizer-cli learn` — structured self-teaching prompt.
- `visualizer-cli explain <path>` — markdown docs for any noun/verb.
- `visualizer-cli overview` — descriptive snapshot of the agent.
- `visualizer-cli doctor` — check the agent-identity invariants.
- `visualizer-cli cli overview` — describe the CLI surface.

## Exit-code policy

- `0` success
- `1` user-input error
- `2` environment / setup error
- `3+` reserved

## See also

- `visualizer-cli explain whoami`
- `visualizer-cli explain doctor`
"""

_WHOAMI = """\
# visualizer-cli whoami

Reports the agent's identity from `culture.yaml`: nick (`suffix`), backend,
served model, and the package version. Read-only.

## Usage

    visualizer-cli whoami
    visualizer-cli whoami --json
"""

_LEARN = """\
# visualizer-cli learn

Prints a structured self-teaching prompt covering purpose, command map,
exit-code policy, `--json` support, and the `explain` pointer.

## Usage

    visualizer-cli learn
    visualizer-cli learn --json
"""

_EXPLAIN = """\
# visualizer-cli explain <path>

Prints markdown documentation for any noun/verb path. Unlike `--help` (terse,
positional), `explain` is global and addressable by path.

## Usage

    visualizer-cli explain visualizer-cli
    visualizer-cli explain whoami
    visualizer-cli explain --json <path>
"""

_OVERVIEW = """\
# visualizer-cli overview

Read-only descriptive snapshot of the agent: identity (from `culture.yaml`), the
verb surface, and the sibling-pattern artifacts the template carries. Accepts an
ignored `target` so a stray path never hard-fails.

## Usage

    visualizer-cli overview
    visualizer-cli overview --json
"""

_DOCTOR = """\
# visualizer-cli doctor

Checks the agent-identity invariants `steward doctor` verifies:
prompt-file-present and backend-consistency (`claude` → `CLAUDE.md`), plus a
skills-present check. Exits 1 when unhealthy.

prompt-file-present requires the *resident* prompt the declared backend
actually reads. Other harness prompt files recognized under the same backend
name (`AGENTS.override.md`, `.pi/SYSTEM.md`, `QWEN.md`) belong to
interactively available harnesses the mesh daemon never loads; they are
reported by the informational harness-prompts check and never substituted.

## Usage

    visualizer-cli doctor
    visualizer-cli doctor --json
"""

_CLI = """\
# visualizer-cli cli

Noun group for CLI-surface introspection. `cli overview` describes the CLI
itself (distinct from the global `overview`, which describes the agent).

## Usage

    visualizer-cli cli overview
    visualizer-cli cli overview --json
"""


ENTRIES: dict[tuple[str, ...], str] = {
    (): _ROOT,
    ("visualizer-cli",): _ROOT,
    ("visualizer",): _ROOT,
    ("whoami",): _WHOAMI,
    ("learn",): _LEARN,
    ("explain",): _EXPLAIN,
    ("overview",): _OVERVIEW,
    ("doctor",): _DOCTOR,
    ("cli",): _CLI,
    ("cli", "overview"): _CLI,
}
