N = int(input())


def solve():
    X, Y, T = map(int, input().split())

    spots = [["."] * X for _ in range(Y)]

    for row in spots[::2]:
        for i in range(0, (X + 1) // 4 * 4, 4):
            for j in range(3):
                row[i + j] = "X"

    for col in range((X + 1) // 4 * 4, X, 2):
        for y, row in enumerate(spots):
            if (y + 1) % 4 == 0:
                continue

            if y >= (Y + 1) // 4 * 4:
                break

            row[col] = "X"

    for row in spots:
        print("".join(row))

    print()


for _ in range(N):
    solve()
