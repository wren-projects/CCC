N = int(input())


def solve():
    X, Y, _ = map(int, input().split())

    spots = [["."] * X for _ in range(Y)]

    for y in range(0, (Y - 1) // 2 * 2, 2):
        for x in range(0, (X - 1) // 3 * 3, 3):
            for i in range(2):
                spots[y][x + i] = "X"

    dx = X - (X - 1) // 3 * 3
    dy = Y - (Y - 1) // 2 * 2

    match dy:
        case 0:
            pass
        case 1:
            for y in range((Y - 1) // 2 * 2, Y):
                for x in range(0, (X - 1) // 3 * 3, 3):
                    for i in range(2):
                        spots[y][x + i] = "X"
        case 2:
            for x in range(0, (X - dx) // 2 * 2, 2):
                for j in range(2):
                    spots[(Y - 1) // 2 * 2 + j][x] = "X"

    # print(dx, dy)
    match dx:
        case 0:
            pass
        case 1:
            for y in range(0, (Y - 1) // 2 * 2 - 2, 3):
                for i in range(2):
                    spots[y + i][X - 1] = "X"
        case 2:
            for y in range(0, (Y - 1) // 2 * 2, 2):
                for i in range(2):
                    spots[y][(X - 1) // 3 * 3 + i] = "X"
        case 3:
            for x in range((X - 1) // 3 * 3, X, 2):
                for y in range(0, Y - dy - 2, 3):
                    for i in range(2):
                        spots[y + i][x] = "X"

    match dx, dy:
        case 3, 2:
            if (Y - 3) % 3 == 0 and (X - 4) % 2 == 0:
                for j in range(Y - 3, Y, 2):
                    for i in range(2):
                        spots[j][X - i - 1] = "X"
                spots[Y - 2][X - 4] = "X"
                spots[Y - 1][X - 4] = "X"
            elif (Y - 4) % 3 == 0:
                spots[Y - 1][X - 3] = "X"
                spots[Y - 2][X - 3] = "X"

                spots[Y - 1][X - 1] = "X"
                spots[Y - 2][X - 1] = "X"

                spots[Y - 4][X - 2] = "X"
                spots[Y - 4][X - 1] = "X"
            else:
                spots[Y - 1][X - 3] = "X"
                spots[Y - 2][X - 3] = "X"

                spots[Y - 1][X - 1] = "X"
                spots[Y - 2][X - 1] = "X"

    patterna_magicka = [
        # VSS
        [
            [Y - 1, X - 3, "X"],
            [Y - 2, X - 3, "X"],
            [Y - 1, X - 1, "X"],
            [Y - 2, X - 1, "X"],
            [Y - 4, X - 2, "X"],
            [Y - 4, X - 1, "X"],
        ],
        # VVS
        [
            [Y - 3, X - 2, "X"],
            [Y - 3, X - 1, "X"],
            [Y - 1, X - 2, "X"],
            [Y - 1, X - 1, "X"],
            [Y - 4, X - 1, "X"],
            [Y - 4, X - 2, "X"],
        ],
        # SS
        [
            [Y - 1, X - 3, "X"],
            [Y - 2, X - 3, "X"],
            [Y - 1, X - 1, "X"],
            [Y - 2, X - 1, "X"],
        ],
        # VV
        [
            [Y - 3, X - 2, "X"],
            [Y - 3, X - 1, "X"],
            [Y - 1, X - 2, "X"],
            [Y - 1, X - 1, "X"],
        ],
        [
            # VS
            [Y - 1, X - 2, "X"],
            [Y - 1, X - 1, "X"],
            [Y - 3, X - 1, "X"],
            [Y - 4, X - 1, "X"],
        ],
        [
            # VS
            [Y - 1, X - 4, "X"],
            [Y - 1, X - 3, "X"],
            [Y - 1, X - 1, "X"],
            [Y - 2, X - 1, "X"],
        ],
        # V
        [
            [Y - 1, X - 2, "X"],
            [Y - 1, X - 1, "X"],
        ],
        # S
        [
            [Y - 1, X - 1, "X"],
            [Y - 2, X - 1, "X"],
        ],
    ]

    OFFSETS = [[-1, -1], [-1, 0], [0, -1], [0, 0]]

    for pattern in patterna_magicka:
        try:
            for y, x, c in pattern:
                breaking = False
                for dx, dy in OFFSETS:
                    if spots[y + dy][x + dx] == ".":
                        pass
                    else:
                        # print("BREAK because", x, y, dx, dy)
                        breaking = True
                        break
                if breaking:
                    break
            else:
                for y, x, c in pattern:
                    # print(x, y, c)
                    spots[y][x] = c
                break
        except Exception as e:
            pass

    for row in spots:
        print("".join(row))

    print()


for _ in range(N):
    solve()
