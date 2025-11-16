from copy import deepcopy

_input = input
input = lambda: _input().strip()

N = int(input())


def solve():
    W, H = map(int, input().split())

    field = [list(input()) for _ in range(H)]

    movements = list(input())

    for start_x in range(W):
        for start_y in range(H):
            x, y = start_x, start_y

            if field[y][x] == "X":
                continue

            current_field = deepcopy(field)
            current_field[y][x] = "X"

            for movement in movements:
                if movement == "D":
                    x += 1
                elif movement == "A":
                    x -= 1
                elif movement == "W":
                    y -= 1
                elif movement == "S":
                    y += 1

                if x < 0 or x >= W or y < 0 or y >= H or current_field[y][x] == "X":
                    break

                current_field[y][x] = "X"
            else:
                if not all(all(tile == "X" for tile in row) for row in current_field):
                    continue

                print("VALID")
                return

    print("INVALID")


for _ in range(N):
    solve()
