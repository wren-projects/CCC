"""Typed replacements for ``print`` and ``print_output``."""

from __future__ import annotations

import builtins
import os
import sys
from typing import TextIO

_output: TextIO | None = None
_console: TextIO | None = None
_dev = True


def configure(
    output: TextIO | None = None,
    *,
    dev: bool = False,
    console: TextIO | None = None,
) -> None:
    """Set the output stream and debug mode."""

    global _output, _console, _dev
    _output = output
    _console = console or sys.__stdout__ or sys.stdout
    _dev = dev


def reset() -> None:
    """Restore standalone defaults."""

    configure(None, dev=True, console=sys.__stdout__ or sys.stdout)


def print(
    *values: object,
    sep: str | None = " ",
    end: str | None = "\n",
    file: TextIO | None = None,
    flush: bool = False,
) -> None:
    """Print debug output when the CLI runs with ``--dev``."""

    if not _dev:
        return

    builtins.print(
        *values,
        sep=sep,
        end=end,
        file=file or _console,
        flush=flush,
    )


def print_output(
    *values: object,
    sep: str | None = " ",
    end: str | None = "\n",
    file: TextIO | None = None,
    flush: bool = False,
) -> None:
    """Write output for ``ccc send``."""

    target = file or _output
    if target is None:
        target = sys.__stdout__ or sys.stdout

    builtins.print(
        *values,
        sep=sep,
        end=end,
        file=target,
        flush=flush,
    )


# The CLI sends debug output to stderr; standalone runs use stdout.
if os.environ.get("CCC_CLI"):
    configure(
        None,
        dev=os.environ.get("CCC_DEV") == "1",
        console=sys.stderr,
    )
else:
    reset()
