"""``scripts/check-file-length.py`` must catch an oversized file — and only that."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check-file-length.py"


def _load():
    """Import scripts/check-file-length.py by path (scripts/ is not a package)."""
    spec = importlib.util.spec_from_file_location("check_file_length", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cfl = _load()


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


def _write_lines(path: Path, n: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x = 1\n" * n, encoding="utf-8")
    return path


def test_the_cap_is_400() -> None:
    assert cfl.load_max_lines(REPO_ROOT) == 400


@pytest.mark.parametrize(
    ("pyproject", "needle"),
    [
        ("[tool.file-length]\nmax-lines = 0\n", "max-lines must be a positive integer"),
        ("[tool.file-length\n", "invalid TOML"),
        ("[tool]\nfile-length = 5\n", "[tool.file-length] must be a table"),
        ('tool = "x"\n', "[tool] must be a table"),
        ('[tool.file-length]\nfile-types = ".py"\n', "file-types must be a non-empty list"),
    ],
)
def test_a_broken_config_in_the_scripts_own_repo_is_a_clean_exit_2(
    tmp_path: Path, pyproject: str, needle: str
) -> None:
    """Regression: the config used to be loaded at import, so a bad pyproject
    next to the script crashed with a traceback and exit 1 (the "oversized"
    code). Run a copy *without* --repo so its own REPO_ROOT is the bad repo."""
    (tmp_path / "scripts").mkdir()
    script = tmp_path / "scripts" / SCRIPT.name
    script.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    _write_lines(tmp_path / "a.py", 1)
    proc = subprocess.run(
        [sys.executable, str(script), str(tmp_path / "a.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert needle in proc.stderr
    assert proc.stderr.startswith("error: ")
    assert "Traceback" not in proc.stderr
    assert proc.stdout == ""


@pytest.mark.parametrize("cap", ["0", "-1"])
def test_a_non_positive_max_is_an_error(tmp_path: Path, cap: str) -> None:
    _write_lines(tmp_path / "a.py", 1)
    proc = _run("--repo", str(tmp_path), "--max", cap, str(tmp_path / "a.py"))
    assert proc.returncode == 2
    assert "--max must be a positive integer" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_a_path_outside_the_repo_is_an_error(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = _write_lines(tmp_path / "elsewhere.py", 1)
    proc = _run("--repo", str(repo), str(outside))
    assert proc.returncode == 2
    assert "is outside the repo" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_the_cap_is_configured_in_pyproject() -> None:
    assert cfl.load_max_lines(REPO_ROOT) == 400
    assert "[tool.file-length]" in (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_the_cap_follows_the_target_repos_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.file-length]\nmax-lines = 10\n", encoding="utf-8"
    )
    _write_lines(tmp_path / "mid.py", 11)
    proc = _run("--repo", str(tmp_path), str(tmp_path / "mid.py"))
    assert proc.returncode == 1
    assert "mid.py: 11 lines (max 10)" in proc.stderr


def test_file_types_are_configured_in_pyproject() -> None:
    types = cfl.load_file_types(REPO_ROOT)
    assert ".py" in types
    assert ".tsx" in types


def test_file_types_follow_the_target_repos_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.file-length]\nmax-lines = 10\nfile-types = [".ts"]\n', encoding="utf-8"
    )
    _write_lines(tmp_path / "big.ts", 11)
    _write_lines(tmp_path / "big.py", 11)
    proc = _run("--repo", str(tmp_path), str(tmp_path / "big.ts"), str(tmp_path / "big.py"))
    assert proc.returncode == 1
    assert "big.ts: 11 lines (max 10)" in proc.stderr
    assert "big.py" not in proc.stderr


def test_bad_file_types_are_an_error(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.file-length]\nfile-types = ["py"]\n', encoding="utf-8"
    )
    _write_lines(tmp_path / "a.py", 1)
    proc = _run("--repo", str(tmp_path), str(tmp_path / "a.py"))
    assert proc.returncode == 2
    assert "file-types" in proc.stderr


def test_a_missing_table_falls_back_and_a_bad_cap_is_an_error(tmp_path: Path) -> None:
    assert cfl.load_max_lines(tmp_path) == cfl.DEFAULT_MAX_LINES
    assert cfl.load_file_types(tmp_path) == cfl.DEFAULT_FILE_TYPES
    (tmp_path / "pyproject.toml").write_text(
        "[tool.file-length]\nmax-lines = 0\n", encoding="utf-8"
    )
    _write_lines(tmp_path / "a.py", 1)
    proc = _run("--repo", str(tmp_path), str(tmp_path / "a.py"))
    assert proc.returncode == 2
    assert "positive integer" in proc.stderr


def test_the_real_repo_is_within_the_cap() -> None:
    """The gate CI runs: every tracked source file is at or under 400 lines."""
    proc = _run()
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr == ""
    assert "within 400 lines" in proc.stdout


def test_a_file_at_the_cap_passes_and_one_over_fails(tmp_path: Path) -> None:
    at_cap = _write_lines(tmp_path / "at.py", 400)
    over = _write_lines(tmp_path / "over.py", 401)
    found = cfl.find_oversized(tmp_path, ["at.py", "over.py"], 400)
    assert found == [("over.py", 401)]
    assert at_cap.is_file()
    assert over.is_file()


def test_an_oversized_file_fails_with_its_name_on_stderr(tmp_path: Path) -> None:
    _write_lines(tmp_path / "big.py", 401)
    proc = _run("--repo", str(tmp_path), str(tmp_path / "big.py"))
    assert proc.returncode == 1
    assert "big.py: 401 lines (max 400)" in proc.stderr
    assert "big.py" not in proc.stdout


def test_max_overrides_the_cap(tmp_path: Path) -> None:
    _write_lines(tmp_path / "mid.py", 50)
    proc = _run("--repo", str(tmp_path), "--max", "40", str(tmp_path / "mid.py"))
    assert proc.returncode == 1
    assert "mid.py: 50 lines (max 40)" in proc.stderr


def test_an_unterminated_last_line_counts(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("a\nb", encoding="utf-8")
    (tmp_path / "b.py").write_text("a\nb\n", encoding="utf-8")
    (tmp_path / "c.py").write_text("", encoding="utf-8")
    assert cfl.count_lines(tmp_path / "a.py") == 2
    assert cfl.count_lines(tmp_path / "b.py") == 2
    assert cfl.count_lines(tmp_path / "c.py") == 0


def test_vendored_skills_and_non_python_files_are_not_checked() -> None:
    assert cfl.is_checked("visualizer_cli/cli/__init__.py")
    assert cfl.is_checked("scripts/harness-smoke.py")
    assert cfl.is_checked("tests/test_cli.py")
    assert not cfl.is_checked(".claude/skills/version-bump/scripts/bump.py")
    assert not cfl.is_checked("CHANGELOG.md")
    assert not cfl.is_checked("uv.lock")
