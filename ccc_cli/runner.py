"""Run a level's main.py against one input file in a subprocess."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunResult:
    input_path: Path
    output_path: Path
    expected_path: Path | None
    duration: float
    output: str
    error: str | None = None
    matches_expected: bool | None = None


def solution_file(folder: Path) -> Path | None:
    path = folder / "main.py"
    return path if path.is_file() else None


def _env(dev: bool) -> dict[str, str]:
    environment = os.environ.copy()
    environment["CCC_CLI"] = "1"
    environment["CCC_DEV"] = "1" if dev else "0"

    # Make ccc_cli importable from the level directory.
    package_root = str(Path(__file__).resolve().parent.parent)
    entries = [package_root, *(entry for entry in sys.path if entry)]
    environment["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(entries))
    return environment


def run_solution(
    folder: Path,
    input_path: Path,
    output_path: Path,
    expected_path: Path | None = None,
    *,
    dev: bool = False,
) -> RunResult:
    folder = folder.resolve()
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    if expected_path is not None:
        expected_path = expected_path.resolve()
    solution = solution_file(folder)

    if solution is None:
        return RunResult(
            input_path=input_path,
            output_path=output_path,
            expected_path=expected_path,
            duration=0.0,
            output="",
            error=f"No main.py found in {folder}",
        )

    console = sys.stdout
    started = time.perf_counter()
    error: str | None = None

    try:
        with (
            input_path.open("r", encoding="utf-8") as input_file,
            output_path.open("w", encoding="utf-8") as output_file,
        ):
            process = subprocess.Popen(
                [sys.executable, str(solution)],
                cwd=folder,
                stdin=input_file,
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env=_env(dev),
            )
            assert process.stdout is not None
            for line in process.stdout:
                output_file.write(line)
                if dev:
                    console.write(line)

            return_code = process.wait()
            if return_code != 0:
                error = f"Solution exited with code {return_code}"
    except OSError as exception:
        error = f"Could not run the solution: {exception}"

    duration = time.perf_counter() - started
    try:
        output = output_path.read_text(encoding="utf-8")
    except OSError:
        output = ""

    expected_path = expected_path if expected_path and expected_path.is_file() else None
    matches: bool | None = None
    if expected_path is not None:
        matches = output.strip() == expected_path.read_text(encoding="utf-8").strip()

    return RunResult(
        input_path=input_path,
        output_path=output_path,
        expected_path=expected_path,
        duration=duration,
        output=output,
        error=error,
        matches_expected=matches,
    )
