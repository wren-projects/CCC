#!/bin/sh
for f in data/in_level-*.txt; do
  [ -e "$f" ] || continue
  python main.py <"$f" >"$f".out
done
