N = int(input())


def solve(X: int) -> list[int]:
    i = -1
    moves = [0]
    if X % 2 == 0:
        for i in range(abs(X) // 2):
            moves.append(max(5 - i, 1))

        moves += moves[::-1]
    else:
        for i in range((abs(X) - 1) // 2):
            moves.append(max(5 - i, 1))

        moves += [max(4 - i, 1)] + moves[::-1]

    if X < 0:
        moves = [-1 * move for move in moves]

    return moves


for _ in range(N):
    Xs, Ys = map(int, input().split()[0].split(","))

    moves_x = solve(Xs)
    moves_y = solve(Ys)

    print(*moves_x)
    print(*moves_y)
