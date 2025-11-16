N = int(input())

for _ in range(N):
    nums = [*map(int, input().split())]

    pos_count = 0
    neg_count = 0
    zero_count = 0

    for num in nums:
        if num > 0:
            pos_count += 1
        elif num < 0:
            neg_count += 1
        else:
            zero_count += 1

    sum_abs = sum(map(abs, nums))

    print(pos_count - neg_count, sum_abs + zero_count)
