# Cloudflight Coding Contest

Solutions for the Cloudflight Coding Contest, plus a small `ccc` CLI for
downloading levels, running solutions and submitting them to
[CatCoder](https://codingcontest.org/).

## Install

```bash
uv sync
```

Use `uv run ccc ...`, or activate `.venv` and run `ccc ...`.

## Setup

Open the training contest in the browser, for example
`https://codingcontest.org/contests/<contest-name>/game`, and copy
`<contest-name>` from the URL. Then copy the `SESSION` and `XSRF-TOKEN`
cookies from your browser's developer tools:

```bash
ccc setup <contest-name> <session-cookie> [xsrf-token]
```

A shorter game slug such as `ccc-2025.11-classic-spaceship` is also accepted;
the CLI starts or resumes an exploration training session for it.

Credentials are stored in `~/.config/ccc/ccc.json`.

## Commands

```bash
ccc new                 # download the current level
ccc new 3               # download level 3
ccc solve               # run the newest local level
ccc solve 3             # run level 3
ccc solve 3 1           # run subtask 1 of level 3
ccc solve 3 --example   # only example inputs
ccc solve 3 --dev       # show print() debug output
ccc send                # submit the newest local level
ccc send 3              # submit level 3
ccc send 3 1            # submit subtask 1 of level 3
```

Levels live in `<year>/level<n>/`, with the year taken from the game slug
(for example `2025` for `ccc-2025.11-classic-spaceship`). `ccc new` puts all
downloaded files in `<level>/data/`, next to `main.py`, and moves the level
PDF to the level directory.

Downloaded levels contain inputs named `in_level-1_1-small.txt`, an example
input and output, and a PDF description:

```text
2025/level1/
  main.py
  level-1.pdf
  data/
    in_level-1_0-example.txt
    out_level-1_0-example.txt
    in_level-1_1-small.txt
    in_level-1_1-small.txt.out
    in_level-1_2-large.txt
    in_level-1_2-large.txt.out
```

`ccc solve` writes `<input>.out` for every input and compares it with the
example's `out_level-...txt` when that file exists. `ccc send` uploads the
non-example outputs to the live game server and prints the judge's verdict,
plus the first few wrong lines when a submission is rejected.

Delete a level's `data/` folder and run `ccc new <level>` again to refresh it.

## Solution template

`ccc new` creates a `main.py` like this:

```python
from ccc_cli.runtime import print, print_output


def solve() -> None:
    n = int(input())

    for _ in range(n):
        line = input()
        print("read:", line)   # debug output, shown with --dev
        print_output(line)     # written to the .out file and submitted


if __name__ == "__main__":
    solve()
```

`print` is silent unless `--dev` is used; `print_output` is what gets submitted.
