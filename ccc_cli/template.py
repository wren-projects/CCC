"""Cloudflight Coding Contest solution."""

from ccc_cli.runtime import print, print_output


def solve() -> None:
    n = int(input())

    for _ in range(n):
        # print is debug-only; print_output is submitted.
        line = input()
        print("read:", line)
        print_output(line)


if __name__ == "__main__":
    solve()
