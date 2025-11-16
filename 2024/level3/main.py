N = int(input())


def solve():
    X, Y, _ = map(int, input().split())

    spots = [[0] * X for _ in range(Y)]

    id = 1

    for row in spots:
        for x in range((X // 3) * 3):
            row[x] = (id + 2) // 3
            id += 1

    for x in range((X // 3) * 3, X):
        for y, row in enumerate(spots):
            if y >= (Y // 3) * 3:
                break

            row[x] = (id + 2) // 3
            id += 1

    for row in spots:
        print(" ".join(map(str, row)))

    print()


for _ in range(N):
    solve()
