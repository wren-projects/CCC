for f in $(ls *.in); do
  python main.py <"$f" >"$f".out; done
