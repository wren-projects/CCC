N = int(input())

lines = [input() for _ in range(N)]

for line in lines:
    max_left = 0
    max_right = 0

    max_up = 0
    max_down = 0

    current_horizontal = 0
    current_vertical = 0

    for ch in line:
        if ch == "W":
            current_vertical += 1
        elif ch == "A":
            current_horizontal -= 1
        elif ch == "S":
            current_vertical -= 1
        elif ch == "D":
            current_horizontal += 1

        if current_horizontal < max_left:
            max_left = current_horizontal
        if current_horizontal > max_right:
            max_right = current_horizontal
        if current_vertical > max_up:
            max_up = current_vertical
        if current_vertical < max_down:
            max_down = current_vertical

    print(max_right - max_left + 1, max_up - max_down + 1)
