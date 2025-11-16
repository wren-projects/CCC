N = int(input())


def solve():
    X, _ = map(int, input().split())

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

    print(*moves, sep=" ")


for _ in range(N):
    solve()
