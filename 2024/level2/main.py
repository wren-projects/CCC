N = int(input())


dimensions = [list(map(int, input().split())) for _ in range(N)]

for x, y, tables in dimensions:
    for j in range(y):
        numbers = []
        for i in range(x):
            numbers.append(str((i + 3) // 3 + j * (x // 3)))

        print(" ".join(numbers))

    print()
