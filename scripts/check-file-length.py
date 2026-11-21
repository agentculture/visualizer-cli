#!/usr/bin/env python3
"""Fail when a tracked source file grows past the line cap.

Every tracked source file in this repo (by default Python; see
``file-types``) — the package, ``scripts/`` and ``tests/`` alike — must stay
at or under ``MAX_LINES`` lines. Long files are where review attention runs
out; the cap forces a split into focused modules before that happens, rather
than after.

The cap and the checked file types are read from ``pyproject.toml``
(``[tool.file-length] max-lines`` and ``file-types``) so they are
configuration, not code. ``DEFAULT_MAX_LINES`` / ``DEFAULT_FILE_TYPES`` apply
only when the table or a key is absent.

Excluded:

* ``.claude/skills/**`` — the guildmaster skill kit is cited verbatim and must
  never be edited here, so it cannot be held to this repo's cap (re-sync from
  upstream instead; see ``docs/skill-sources.md``).

Usage:
    check-file-length.py                 # check all tracked files (git ls-files)
    check-file-length.py path [path...]  # check specific files
    check-file-length.py --max N         # override the cap (default: pyproject.toml)

Output contract (the repo's): a one-line result on stdout; each offending file
on stderr as ``path: N lines (max M)``. Exit 0 when every file is within the
cap, 1 when any file exceeds it, 2 when ``git ls-files`` cannot run or the
configured cap is invalid.
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


def _table(repo: Path) -> dict:
    pyproject = repo / "pyproject.toml"
    if not pyproject.is_file():
        return {}
    tool = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("tool", {})
    return tool.get("file-length", {})


def load_max_lines(repo: Path) -> int:
    """The cap from ``repo/pyproject.toml`` ``[tool.file-length] max-lines``."""
    value = _table(repo).get("max-lines", DEFAULT_MAX_LINES)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"[tool.file-length] max-lines must be a positive integer, got {value!r}")
    return value


def load_file_types(repo: Path) -> tuple[str, ...]:
    """Checked extensions from ``repo/pyproject.toml`` ``[tool.file-length] file-types``."""
    value = _table(repo).get("file-types", list(DEFAULT_FILE_TYPES))
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(v, str) and v.startswith(".") for v in value)
    ):
        raise ValueError(
            f"[tool.file-length] file-types must be a non-empty list like ['.py'], got {value!r}"
        )
    return tuple(value)


#: The cap and file types configured for this repo. Change them in
#: pyproject.toml, not here.
MAX_LINES = load_max_lines(REPO_ROOT)
CHECKED_SUFFIXES = load_file_types(REPO_ROOT)

#: Path prefixes (repo-relative, POSIX) never checked — see the docstring.
EXCLUDED_PREFIXES = (".claude/skills/",)


def is_checked(rel: str, suffixes: tuple[str, ...] | None = None) -> bool:
    """Whether a repo-relative path is held to the cap."""
    exts = CHECKED_SUFFIXES if suffixes is None else suffixes
    return rel.endswith(exts) and not rel.startswith(EXCLUDED_PREFIXES)


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
    repo: Path, paths: list[str], max_lines: int, suffixes: tuple[str, ...] | None = None
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
    try:
        suffixes = load_file_types(repo)
        if args.max is None:
            args.max = load_max_lines(repo)
    except (ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.paths:
        paths = [Path(p).resolve().relative_to(repo).as_posix() for p in args.paths]
    else:
        try:
            paths = tracked_files(repo)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"error: could not list tracked files: {exc}", file=sys.stderr)
            return 2

    checked = [p for p in paths if is_checked(p, suffixes)]
    oversized = find_oversized(repo, checked, args.max, suffixes)
    for rel, lines in oversized:
        print(f"{rel}: {lines} lines (max {args.max})", file=sys.stderr)

    if oversized:
        print(f"file length: {len(oversized)} of {len(checked)} file(s) over {args.max} lines")
        return 1
    print(f"file length: all {len(checked)} file(s) within {args.max} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
