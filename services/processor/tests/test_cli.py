"""End-to-end CLI tests via subprocess (same callable, JSON on stdout)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def run_cli(*args: str, env_extra: dict[str, str] | None = None):
    env = {
        **os.environ,
        "TRANSCRIPTION_MODE": "mock",
        "ANALYSIS_MODE": "mock",
    }
    env.pop("GEMINI_API_KEY", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "services.processor.cli", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_cli_prints_json_to_stdout(mp4_path: Path) -> None:
    completed = run_cli(str(mp4_path))

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert set(result) == {"transcript", "analysis"}
    assert result["transcript"].strip()
    assert result["analysis"]["sentiment"] in {"positive", "negative", "neutral"}


def test_cli_marks_mock_output_as_synthetic(mp4_path: Path) -> None:
    completed = run_cli(str(mp4_path))

    assert completed.returncode == 0, completed.stderr
    assert "SYNTHETIC" in completed.stderr


def test_cli_diagnostics_only_on_stderr(mp4_path: Path) -> None:
    completed = run_cli(str(mp4_path))

    # stdout must stay pipeable to python -m json.tool.
    json.loads(completed.stdout)


def test_cli_missing_file_exits_nonzero(tmp_path: Path) -> None:
    completed = run_cli(str(tmp_path / "nope.mp4"))

    assert completed.returncode == 1
    assert "error:" in completed.stderr
    assert completed.stdout.strip() == ""


def test_cli_not_implemented_mode_fails_loudly(mp4_path: Path) -> None:
    completed = run_cli(str(mp4_path), env_extra={"TRANSCRIPTION_MODE": "faster_whisper"})

    assert completed.returncode == 1
    assert "P2" in completed.stderr


def test_cli_invalid_mode_fails_loudly(mp4_path: Path) -> None:
    completed = run_cli(str(mp4_path), env_extra={"ANALYSIS_MODE": "gpt5"})

    assert completed.returncode == 1
    assert "Invalid ANALYSIS_MODE" in completed.stderr
