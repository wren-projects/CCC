"""``ccc`` command line interface."""

from __future__ import annotations

import argparse
import contextlib
import difflib
import getpass
import io
import os
import re
import shutil
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from . import __version__
from .api import Api, ApiError
from .config import ConfigError, load_config, save_config
from .runner import RunResult, run_solution
from .tasks import (
    Task,
    TaskError,
    data_folder,
    find_inputs,
    find_outputs,
    new_task_folder,
    parse_level,
    resolve_task,
    select_inputs,
    select_outputs,
)

TEMPLATE = Path(__file__).with_name("template.py").read_text(encoding="utf-8")


def _style(text: str, code: str) -> str:
    if sys.stdout.isatty() and not os.environ.get("NO_COLOR"):
        return f"\033[{code}m{text}\033[0m"
    return text


def _green(text: str) -> str:
    return _style(text, "32")


def _red(text: str) -> str:
    return _style(text, "31")


def _yellow(text: str) -> str:
    return _style(text, "33")


def _bold(text: str) -> str:
    return _style(text, "1")


def _error(message: str) -> None:
    print(_red(f"Error: {message}"), file=sys.stderr)


def _safe_extract(zip_data: bytes, destination: Path) -> None:
    destination = destination.resolve()
    try:
        archive = ZipFile(io.BytesIO(zip_data))
    except BadZipFile as error:
        raise ApiError("The input download is not a valid zip file.") from error

    with archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(destination):
                raise ApiError(f"Refusing to extract unsafe path {member.filename!r}.")
            if target.name in {"main.py", "solve"}:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


def _move_visualizer(data: Path, folder: Path) -> Path | None:
    html_files = sorted(
        path
        for path in data.rglob("*")
        if path.is_file() and path.suffix.lower() in {".html", ".htm"}
    )
    if not html_files:
        return None
    target = folder / "visualizer.html"
    html_files[0].replace(target)
    return target


def cmd_setup(args: argparse.Namespace) -> int:
    config = load_config()
    config.contest_id = str(args.contest_id).strip()
    if not config.contest_id:
        raise ConfigError("Contest name cannot be empty.")

    if args.session_cookie:
        config.session_cookie = args.session_cookie
    elif not config.session_cookie:
        if not sys.stdin.isatty():
            raise ConfigError("Session cookie was not provided.")
        config.session_cookie = getpass.getpass("Session cookie: ").strip()

    if args.xsrf_token is not None:
        config.xsrf_token = args.xsrf_token

    path = save_config(config)
    print(f"Configuration saved to {path}")

    api = Api(config)
    try:
        username = api.current_user()
    except ApiError as error:
        print(_yellow(f"Could not verify the session: {error}"))
        return 1

    print(f"Logged in as {_bold(username)}")

    try:
        contest = api.resolve_contest(config.contest_id)
    except ApiError as error:
        print(_yellow(f"Could not find the contest: {error}"))
        return 1

    name = contest.get("name") or config.contest_id
    game_name = contest.get("gameName")
    details = f" ({game_name})" if game_name else ""
    print(f"Contest: {_bold(str(name))}{details}")
    return 0


def _year_from_game_slug(slug: object) -> int | None:
    if not slug:
        return None
    match = re.search(r"(?<!\d)(\d{4})(?!\d)", str(slug))
    return int(match.group(1)) if match else None


def cmd_new(args: argparse.Namespace) -> int:
    config = load_config(required=True)
    api = Api(config)
    contest = api.resolve_contest(config.contest_id)
    game = api.game(contest)

    level = parse_level(args.level) if args.level else game.current_level()
    total_levels = contest.get("totalLevels")
    if isinstance(total_levels, int) and not 1 <= level <= total_levels:
        raise TaskError(
            f"Level {level} is not available; this game has levels 1-{total_levels}."
        )

    year = _year_from_game_slug(contest.get("gameSlug")) or datetime.now().year
    task = new_task_folder(level, year)
    main_file = task.folder / "main.py"
    data = data_folder(task.folder)

    if main_file.exists() and data.is_dir():
        print(f"Level {task.label} already exists at {task.folder}")
        print("Delete its data/ folder to download the files again.")
        return 0

    game_name = contest.get("gameName") or contest.get("name") or "CatCoder"
    print(f"Level {_bold(str(level))} ({year}) — {game_name}")
    print(f"Logged in as {_bold(api.current_user())}")
    print(f"Downloading level {level}...")

    zip_data = game.download_level_zip(level)

    task.folder.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    (task.folder.parent / f"level{level}.zip").write_bytes(zip_data)
    _safe_extract(zip_data, data)

    pdf_names = [pdf.name for pdf in sorted(data.glob("*.pdf"))]
    for name in pdf_names:
        (data / name).replace(task.folder / name)

    visualizer = _move_visualizer(data, task.folder)

    if main_file.exists():
        print(f"Kept existing {main_file}")
    else:
        main_file.write_text(TEMPLATE, encoding="utf-8")
        print(f"Created {main_file}")

    print(f"Inputs: {data}")
    if pdf_names:
        pdf = task.folder / pdf_names[0]
        print(f"Description: {pdf}")
        if sys.stdout.isatty():
            with contextlib.suppress(webbrowser.Error):
                webbrowser.open(pdf.as_uri())

    if visualizer is not None:
        print(f"Visualizer: {visualizer}")

    print(f"Next: {_bold(f'ccc solve {task.label}')}")
    return 0


def _format_duration(seconds: float) -> str:
    return f"{seconds * 1000:.0f} ms" if seconds < 1 else f"{seconds:.2f} s"


def _show_mismatch(expected: str, actual: str) -> None:
    diff = difflib.unified_diff(
        expected.splitlines(),
        actual.splitlines(),
        fromfile="expected",
        tofile="got",
        lineterm="",
    )
    print("    First differences:")
    for line in list(diff)[:60]:
        print(f"    {line}")


def _run_task(task: Task, subtask: str | None, *, dev: bool) -> bool:
    inputs = find_inputs(task.folder)
    if not inputs:
        raise TaskError(
            f"No input files found in {data_folder(task.folder)}. "
            f"Run `ccc new {task.level}` first."
        )

    selected = select_inputs(inputs, subtask)
    print(f"Solving {_bold(task.label)} ({len(selected)} input(s))")

    failed = False
    for item in selected:
        print(f"  {item.path.name} ... ", end="", flush=True)
        result: RunResult = run_solution(
            task.folder,
            item.path,
            item.output_path,
            expected_path=item.expected_path,
            dev=dev,
        )

        if result.error:
            failed = True
            print(_red("ERROR"))
            print(f"    {result.error}")
        elif result.matches_expected is False:
            failed = True
            print(_red("WRONG"))
            expected = item.expected_path.read_text(encoding="utf-8")
            _show_mismatch(expected, result.output)
        elif result.matches_expected is True:
            print(_green("OK") + f" ({_format_duration(result.duration)})")
        else:
            print(_green("done") + f" ({_format_duration(result.duration)})")

    print()
    print(_red("Some inputs failed.") if failed else _green("All inputs passed."))
    return not failed


def cmd_solve(args: argparse.Namespace) -> int:
    task = resolve_task(args.task)
    subtask = "example" if args.example else args.subtask
    return 0 if _run_task(task, subtask, dev=args.dev) else 1


def _show_evaluation(evaluation: dict[str, object]) -> None:
    file_message = evaluation.get("fileMessage")
    if file_message:
        print(f"    {file_message}")

    cases = evaluation.get("cases")
    if not isinstance(cases, list):
        return

    wrong = [
        case for case in cases if isinstance(case, dict) and not case.get("isCorrect")
    ]
    for case in wrong[:5]:
        message = case.get("caseMessage") or case.get("caseState") or "wrong answer"
        print(f"    {message}")
    if len(wrong) > 5:
        print(f"    ... and {len(wrong) - 5} more wrong line(s)")


def cmd_send(args: argparse.Namespace) -> int:
    config = load_config(required=True)
    task = resolve_task(args.task)

    if args.subtask and args.subtask.lower() == "example":
        raise TaskError("Example outputs are not submitted.")

    outputs = select_outputs(find_outputs(task.folder), args.subtask)
    if not outputs:
        raise TaskError(
            f"No outputs in {data_folder(task.folder)}. Run `ccc solve` first."
        )

    for output in outputs:
        if output.level != task.level:
            raise TaskError(
                f"{output.path.name} belongs to level {output.level}, "
                f"not level {task.level}."
            )

    api = Api(config)
    contest = api.resolve_contest(config.contest_id)
    game = api.game(contest)

    print(f"Sending {_bold(task.label)} ({len(outputs)} output(s))")
    print(f"Logged in as {_bold(api.current_user())}")

    failed = False
    for index, output in enumerate(outputs):
        print(f"  {output.name} ... ", end="", flush=True)
        try:
            content = output.path.read_bytes()
            response = game.submit_solution(
                task.level,
                output.file_id,
                content,
                output.path.name,
            )
        except OSError as error:
            print(_red("ERROR"))
            print(f"    {error}")
            return 1
        except ApiError as error:
            print(_red("ERROR"))
            print(f"    {error}")
            return 1

        evaluation = response.get("evaluation")
        if not isinstance(evaluation, dict):
            print(_red("ERROR"))
            print(f"    Unexpected response: {response!r}")
            return 1

        if evaluation.get("isCorrect"):
            print(_green("✅ VALID"))
        else:
            failed = True
            print(_red("❌ WRONG"))
            _show_evaluation(evaluation)

        cooldown = response.get("cooldownSec")
        if (
            index < len(outputs) - 1
            and isinstance(cooldown, (int, float))
            and cooldown > 0
        ):
            time.sleep(float(cooldown) + 0.5)

    print()
    if failed:
        print(_red("Some submissions were incorrect."))
        return 1

    print(_green("All submissions accepted!"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ccc",
        description="CatCoder CLI for the Cloudflight Coding Contest",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    setup = subparsers.add_parser("setup", help="save CatCoder credentials")
    setup.add_argument(
        "contest_id",
        help="training contest name from /contests/<name>/game (or game slug)",
    )
    setup.add_argument(
        "session_cookie",
        nargs="?",
        help="value of the SESSION cookie (prompted for if omitted)",
    )
    setup.add_argument("xsrf_token", nargs="?", help="value of the XSRF-TOKEN cookie")
    setup.set_defaults(func=cmd_setup)

    new = subparsers.add_parser("new", help="download a level")
    new.add_argument(
        "level",
        nargs="?",
        help="level number; defaults to the current level in the game",
    )
    new.set_defaults(func=cmd_new)

    solve = subparsers.add_parser("solve", help="run against local inputs")
    solve.add_argument(
        "task",
        nargs="?",
        help="level number, level7, 2025/level7 or a level directory",
    )
    solve.add_argument(
        "subtask",
        nargs="?",
        help="subtask number, file ID such as 1-small, 'example' or 'all'",
    )
    solve.add_argument(
        "-d",
        "--dev",
        action="store_true",
        help="show the solution's print() debug output",
    )
    solve.add_argument(
        "--example",
        action="store_true",
        help="only run example inputs",
    )
    solve.set_defaults(func=cmd_solve)

    send = subparsers.add_parser("send", help="submit generated outputs")
    send.add_argument(
        "task",
        nargs="?",
        help="level number, level7, 2025/level7 or a level directory",
    )
    send.add_argument(
        "subtask",
        nargs="?",
        help="subtask number or file ID such as 2-large (default: all)",
    )
    send.set_defaults(func=cmd_send)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        return int(args.func(args))
    except (ApiError, ConfigError, TaskError) as error:
        _error(str(error))
        return 1
    except KeyboardInterrupt:
        print()
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
