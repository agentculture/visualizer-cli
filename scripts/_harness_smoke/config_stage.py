"""Stage ``config`` — offline, always runnable, the load-bearing stage."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from _harness_smoke.common import (
    CANONICAL_SKILLS_REL,
    FAIL,
    FINGERPRINTS_REL,
    HARNESS_BACKEND,
    HARNESSES,
    PASS,
    Result,
    registry_prompts_by_backend,
)


def _check_relative_skills_symlink(repo: Path, rel: str) -> list[str]:
    """A harness skills dir must be a *relative* symlink onto the one kit."""
    problems: list[str] = []
    link = repo / rel
    if not link.is_symlink():
        problems.append(f"{rel} must be a symlink onto {CANONICAL_SKILLS_REL}")
        return problems
    target = os.readlink(link)
    if os.path.isabs(target):
        problems.append(f"{rel} points at an absolute target {target!r}; must be relative")
    canonical = repo / CANONICAL_SKILLS_REL
    if not link.exists() or link.resolve() != canonical.resolve():
        problems.append(f"{rel} does not resolve to {CANONICAL_SKILLS_REL}")
    return problems


def _check_canonical_skill_tree(repo: Path) -> list[str]:
    tree = repo / CANONICAL_SKILLS_REL
    if not tree.is_dir():
        return [f"{CANONICAL_SKILLS_REL} is missing"]
    if not any(tree.glob("*/SKILL.md")):
        return [f"{CANONICAL_SKILLS_REL} holds no <name>/SKILL.md"]
    return []


#: harness -> extra, harness-specific skills-discovery wiring checks.
#:
#: colleague deliberately checks only that `.colleague/skills` is wired, NOT
#: that colleague *loads* those skills: it currently does not, and that is an
#: upstream blocker (agentculture/colleague#494 — configdir.collect_files skips
#: directories, and layers._within rejects symlinks escaping .colleague/). What
#: colleague does resolve today, and what the live stage asserts, is
#: AGENTS.colleague.md.
SKILLS_WIRING: dict[str, Callable[[Path], list[str]]] = {
    "claude": _check_canonical_skill_tree,
    "pi": lambda repo: _check_relative_skills_symlink(repo, ".pi/skills"),
    "qwen": lambda repo: _check_relative_skills_symlink(repo, ".qwen/skills"),
    "colleague": lambda repo: _check_relative_skills_symlink(repo, ".colleague/skills"),
}


def stage_config(repo: Path, harnesses: dict[str, Any]) -> list[Result]:
    results: list[Result] = []
    by_backend = registry_prompts_by_backend(repo)

    for name in HARNESSES:
        spec = harnesses[name]
        resolves = [str(p) for p in (spec.get("resolves") or [])]
        problems: list[str] = []

        if not resolves:
            problems.append("the YAML lists no `resolves` paths for this harness")
        for rel in resolves:
            path = repo / rel
            if not path.is_file():
                problems.append(f"{rel} is missing")
            elif not path.read_text(encoding="utf-8").strip():
                problems.append(f"{rel} is empty")
            backend = HARNESS_BACKEND[name]
            if rel not in by_backend.get(backend, ()):
                problems.append(
                    f"{rel} is not registered under backend '{backend}' in {FINGERPRINTS_REL}"
                )

        problems.extend(SKILLS_WIRING[name](repo))

        if problems:
            results.append(Result("config", name, FAIL, "; ".join(problems)))
        else:
            results.append(
                Result(
                    "config",
                    name,
                    PASS,
                    f"resolves {', '.join(resolves)}; skills discovery wired",
                )
            )

    if by_backend:
        total = sum(len(v) for v in by_backend.values())
        results.append(
            Result(
                "config",
                "fingerprint-registry",
                PASS,
                f"{FINGERPRINTS_REL} registers {total} prompt path(s) "
                f"across {len(by_backend)} backend(s)",
            )
        )
    else:
        results.append(
            Result(
                "config",
                "fingerprint-registry",
                FAIL,
                f"{FINGERPRINTS_REL} is missing, unreadable, or registers no prompt paths",
            )
        )

    bare = repo / "AGENTS.md"
    if bare.exists():
        results.append(
            Result(
                "config",
                "no-bare-agents-md",
                FAIL,
                "AGENTS.md exists; this template ships none on purpose — it would "
                "shadow AGENTS.override.md / AGENTS.colleague.md in the Pi and "
                "colleague prompt cascades",
            )
        )
    else:
        results.append(
            Result("config", "no-bare-agents-md", PASS, "no bare AGENTS.md, as intended")
        )

    return results
