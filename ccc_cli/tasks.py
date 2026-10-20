"""Finding levels, input files, and generated outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

LEVEL_RE = re.compile(r"^level[\s_-]*(\d+)$", re.IGNORECASE)
YEAR_LEVEL_RE = re.compile(r"^(?:(\d{4})[\s/_-]+)?level[\s_-]*(\d+)$", re.IGNORECASE)
YEAR_NUMBER_RE = re.compile(r"^(\d{4})[\s/_-]+(\d+)$")
NUMBER_RE = re.compile(r"^\d+$")
YEAR_DIR_RE = re.compile(r"^\d{4}$")

GAME_INPUT_RE = re.compile(r"^in_level-(\d+)_(.+)\.txt$", re.IGNORECASE)
GAME_OUTPUT_RE = re.compile(r"^in_level-(\d+)_(.+)\.txt\.out$", re.IGNORECASE)


class TaskError(Exception):
    """Raised when a level cannot be found or parsed."""


@dataclass(frozen=True)
class Task:
    year: int | None
    level: int
    folder: Path

    @property
    def label(self) -> str:
        if self.year is not None:
            return f"{self.year}/level{self.level}"
        return f"level{self.level}"


@dataclass(frozen=True)
class InputFile:
    path: Path
    output_path: Path
    expected_path: Path | None


@dataclass(frozen=True)
class OutputFile:
    name: str
    path: Path
    file_id: str
    level: int


def _level_from_folder(folder: Path) -> int | None:
    match = LEVEL_RE.match(folder.name)
    return int(match.group(1)) if match else None


def _task_from_folder(folder: Path) -> Task | None:
    folder = folder.resolve()
    level = _level_from_folder(folder)
    if level is None:
        return None

    year = None
    for part in reversed(folder.parts[:-1]):
        if YEAR_DIR_RE.match(part):
            year = int(part)
            break

    return Task(year=year, level=level, folder=folder)


def parse_level(value: str) -> int:
    """Parse ``7``, ``level7``, ``2025/level7`` or ``2025-level7``."""

    value = value.strip()
    if NUMBER_RE.match(value):
        return int(value)

    match = YEAR_LEVEL_RE.match(value)
    if match:
        return int(match.group(2))

    match = YEAR_NUMBER_RE.match(value)
    if match:
        return int(match.group(2))

    raise TaskError(f"Could not understand level {value!r}.")


def latest_task(root: Path | None = None) -> Task:
    """Find the newest local ``<year>/level<n>`` directory."""

    root = (root or Path.cwd()).resolve()
    candidates: list[Task] = []

    for year_dir in root.iterdir():
        if not year_dir.is_dir() or not YEAR_DIR_RE.match(year_dir.name):
            continue
        for level_dir in year_dir.iterdir():
            task = _task_from_folder(level_dir)
            if task is not None:
                candidates.append(task)

    if not candidates:
        raise TaskError("No levels found. Run `ccc new` first.")

    return max(candidates, key=lambda task: (task.year or 0, task.level))


def resolve_task(value: str | None, root: Path | None = None) -> Task:
    """Resolve a command line level reference to a local directory."""

    root = (root or Path.cwd()).resolve()

    if value is None:
        cwd_task = _task_from_folder(Path.cwd())
        if cwd_task is not None and (Path.cwd() / "main.py").exists():
            return cwd_task
        return latest_task(root)

    path = Path(value).expanduser()
    if path.is_dir():
        task = _task_from_folder(path)
        if task is None:
            raise TaskError(f"Directory {path} does not look like a level.")
        return task

    level = parse_level(value)
    for year_dir in sorted(root.iterdir(), reverse=True):
        if not year_dir.is_dir() or not YEAR_DIR_RE.match(year_dir.name):
            continue
        folder = year_dir / f"level{level}"
        if folder.is_dir():
            return Task(year=int(year_dir.name), level=level, folder=folder.resolve())

    raise TaskError(f"Level {level} not found. Run `ccc new` first.")


def new_task_folder(level: int, year: int) -> Task:
    folder = (Path.cwd() / str(year) / f"level{level}").resolve()
    return Task(year=year, level=level, folder=folder)


def data_folder(folder: Path) -> Path:
    """The folder that holds a level's inputs and outputs."""

    return folder / "data"


def _game_input_parts(path: Path) -> tuple[int, str] | None:
    match = GAME_INPUT_RE.match(path.name)
    if not match:
        return None
    return int(match.group(1)), match.group(2)


def _game_output_parts(path: Path) -> tuple[int, str] | None:
    match = GAME_OUTPUT_RE.match(path.name)
    if not match:
        return None
    return int(match.group(1)), match.group(2)


def _expected_path(path: Path) -> Path | None:
    expected = path.with_name("out_" + path.name.removeprefix("in_"))
    return expected if expected.is_file() else None


def find_inputs(folder: Path) -> list[InputFile]:
    root = data_folder(folder)
    if not root.is_dir():
        return []

    inputs: list[InputFile] = []
    for path in sorted(root.glob("in_level-*.txt")):
        if not path.is_file():
            continue
        expected = _expected_path(path)
        inputs.append(
            InputFile(
                path=path.resolve(),
                output_path=Path(f"{path}.out").resolve(),
                expected_path=expected.resolve() if expected else None,
            )
        )
    return inputs


def subtask_matches(input_file: InputFile, subtask: str | None) -> bool:
    if subtask is None or subtask.lower() in {"", "all"}:
        return True

    subtask = subtask.lower()
    name = input_file.path.name.lower()

    if subtask == "example":
        return "example" in name

    if subtask.isdigit():
        pattern = rf"(?:^|[_\-])0*{int(subtask)}(?:[_\-.]|$)"
        return re.search(pattern, name) is not None

    game = _game_input_parts(input_file.path)
    if game is not None and subtask == game[1].lower():
        return True

    return subtask in {name, input_file.path.stem.lower()}


def select_inputs(inputs: list[InputFile], subtask: str | None) -> list[InputFile]:
    selected = [item for item in inputs if subtask_matches(item, subtask)]
    if not selected:
        available = ", ".join(item.path.name for item in inputs) or "none"
        raise TaskError(
            f"No input files match subtask {subtask!r}. Available: {available}"
        )
    return selected


def find_outputs(folder: Path) -> list[OutputFile]:
    root = data_folder(folder)
    if not root.is_dir():
        return []

    outputs: list[OutputFile] = []
    for path in sorted(root.glob("in_level-*.txt.out")):
        if not path.is_file():
            continue
        parts = _game_output_parts(path)
        if parts is None:
            continue
        level, file_id = parts
        if "example" in file_id.lower():
            continue
        outputs.append(
            OutputFile(
                name=file_id,
                path=path.resolve(),
                file_id=file_id,
                level=level,
            )
        )
    return outputs


def select_outputs(
    outputs: list[OutputFile],
    subtask: str | None,
) -> list[OutputFile]:
    if subtask is None or subtask.lower() in {"", "all"}:
        return outputs

    subtask = subtask.lower()
    selected: list[OutputFile] = []
    for output in outputs:
        name = output.name.lower()
        if subtask.isdigit():
            pattern = rf"(?:^|[_\-])0*{int(subtask)}(?:[_\-.]|$)"
            if re.search(pattern, name):
                selected.append(output)
        elif subtask in {name, output.path.name.lower()}:
            selected.append(output)

    if not selected:
        available = ", ".join(output.name for output in outputs) or "none"
        raise TaskError(f"No outputs match subtask {subtask!r}. Available: {available}")
    return selected
