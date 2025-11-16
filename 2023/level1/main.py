N = int(input())

lines = [input() for _ in range(N)]

for line in lines:
    directions = {"W": 0, "D": 0, "A": 0, "S": 0}
    for ch in line.strip():
        directions[ch] += 1

    print(directions["W"], directions["D"], directions["S"], directions["A"])
