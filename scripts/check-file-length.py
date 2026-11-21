#!/usr/bin/env python3
"""Fail when a tracked source file grows past the line cap.

Every tracked source file in this repo (by default Python; see
``file-types``) — the package, ``scripts/`` and ``tests/`` alike — must stay
at or under the configured cap. Long files are where review attention runs
out; the cap forces a split into focused modules before that happens, rather
than after.

The cap and the checked file types are read from the target repo's
``pyproject.toml`` (``[tool.file-length] max-lines`` and ``file-types``) so
they are configuration, not code. ``DEFAULT_MAX_LINES`` / ``DEFAULT_FILE_TYPES``
apply only when the table or a key is absent. Nothing is read at import time:
a broken config is reported by :func:`main`, never as an import traceback.

Excluded:

* ``.claude/skills/**`` — the guildmaster skill kit is cited verbatim and must
  never be edited here, so it cannot be held to this repo's cap (re-sync from
  upstream instead; see ``docs/skill-sources.md``).

Usage:
    check-file-length.py                 # check all tracked files (git ls-files)
    check-file-length.py path [path...]  # check specific files (inside --repo)
    check-file-length.py --max N         # override the cap (default: pyproject.toml)

Output contract (the repo's): a one-line result on stdout; each offending file
on stderr as ``path: N lines (max M)``. Exit 0 when every file is within the
cap, 1 when any file exceeds it, 2 for anything that prevents a check — an
invalid ``[tool.file-length]`` table (cap or file types) or unparsable
``pyproject.toml``, a non-positive ``--max``, a path outside ``--repo``, or
``git ls-files`` failing. Every exit-2 case is a one-line ``error:`` on
stderr, never a traceback.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 - fixed git invocation only
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Fallbacks when pyproject.toml carries no ``[tool.file-length]`` table/key.
DEFAULT_MAX_LINES = 400
DEFAULT_FILE_TYPES = (".py",)

#: Path prefixes (repo-relative, POSIX) never checked — see the docstring.
EXCLUDED_PREFIXES = (".claude/skills/",)

EXIT_OK = 0
EXIT_OVERSIZED = 1
EXIT_ERROR = 2


class ConfigError(ValueError):
    """``pyproject.toml`` cannot be parsed or its ``[tool.file-length]`` is invalid."""


def _table(repo: Path) -> dict:
    """The ``[tool.file-length]`` table of ``repo/pyproject.toml`` (``{}`` if absent)."""
    pyproject = repo / "pyproject.toml"
    if not pyproject.is_file():
        return {}
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{pyproject}: invalid TOML: {exc}") from exc
    tool = data.get("tool", {})
    if not isinstance(tool, dict):
        raise ConfigError(f"{pyproject}: [tool] must be a table")
    table = tool.get("file-length", {})
    if not isinstance(table, dict):
        raise ConfigError(f"{pyproject}: [tool.file-length] must be a table, got {table!r}")
    return table


def load_max_lines(repo: Path) -> int:
    """The cap from ``repo/pyproject.toml`` ``[tool.file-length] max-lines``."""
    value = _table(repo).get("max-lines", DEFAULT_MAX_LINES)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigError(f"[tool.file-length] max-lines must be a positive integer, got {value!r}")
    return value


def load_file_types(repo: Path) -> tuple[str, ...]:
    """Checked extensions from ``repo/pyproject.toml`` ``[tool.file-length] file-types``."""
    value = _table(repo).get("file-types", list(DEFAULT_FILE_TYPES))
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(v, str) and v.startswith(".") for v in value)
    ):
        raise ConfigError(
            f"[tool.file-length] file-types must be a non-empty list like ['.py'], got {value!r}"
        )
    return tuple(value)


def is_checked(rel: str, suffixes: tuple[str, ...] = DEFAULT_FILE_TYPES) -> bool:
    """Whether a repo-relative path is held to the cap."""
    return rel.endswith(suffixes) and not rel.startswith(EXCLUDED_PREFIXES)


def tracked_files(repo: Path) -> list[str]:
    """Repo-relative paths of every tracked file, via ``git ls-files``."""
    proc = subprocess.run(  # nosec B603,B607 - fixed git invocation
        ["git", "ls-files", "-z"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    return [p for p in proc.stdout.decode("utf-8").split("\0") if p]


def count_lines(path: Path) -> int:
    """Physical line count, matching ``wc -l`` plus an unterminated last line."""
    data = path.read_bytes()
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def find_oversized(
    repo: Path,
    paths: list[str],
    max_lines: int,
    suffixes: tuple[str, ...] = DEFAULT_FILE_TYPES,
) -> list[tuple[str, int]]:
    """``(path, lines)`` for each checked file over ``max_lines``, in input order."""
    oversized: list[tuple[str, int]] = []
    for rel in paths:
        if not is_checked(rel, suffixes):
            continue
        path = repo / rel
        if not path.is_file():  # deleted in the worktree but still tracked
            continue
        lines = count_lines(path)
        if lines > max_lines:
            oversized.append((rel, lines))
    return oversized


def _error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return EXIT_ERROR


def _resolve_paths(repo: Path, raw: list[str]) -> list[str]:
    """Repo-relative POSIX paths; raises ``ValueError`` for a path outside ``repo``."""
    out: list[str] = []
    for p in raw:
        resolved = Path(p).resolve()
        if not resolved.is_relative_to(repo):
            raise ValueError(f"{p} is outside the repo {repo}")
        out.append(resolved.relative_to(repo).as_posix())
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", help="Files to check (default: all tracked files).")
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="Line cap (default: [tool.file-length] max-lines in the repo's pyproject.toml).",
    )
    parser.add_argument("--repo", default=str(REPO_ROOT), help="Repo root.")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    if args.max is not None and args.max <= 0:
        return _error(f"--max must be a positive integer, got {args.max}")
    try:
        suffixes = load_file_types(repo)
        max_lines = args.max if args.max is not None else load_max_lines(repo)
    except ConfigError as exc:
        return _error(str(exc))

    if args.paths:
        try:
            paths = _resolve_paths(repo, args.paths)
        except ValueError as exc:
            return _error(str(exc))
    else:
        try:
            paths = tracked_files(repo)
        except (OSError, subprocess.CalledProcessError) as exc:
            return _error(f"could not list tracked files: {exc}")

    checked = [p for p in paths if is_checked(p, suffixes)]
    oversized = find_oversized(repo, checked, max_lines, suffixes)
    for rel, lines in oversized:
        print(f"{rel}: {lines} lines (max {max_lines})", file=sys.stderr)

    if oversized:
        print(f"file length: {len(oversized)} of {len(checked)} file(s) over {max_lines} lines")
        return EXIT_OVERSIZED
    print(f"file length: all {len(checked)} file(s) within {max_lines} lines")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
