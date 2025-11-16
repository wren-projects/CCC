N = int(input())

dimensions = [list(map(int, input().split())) for _ in range(N)]

for x, y in dimensions:
    print(x // 3 * y + y // 3 * (x % 3))
