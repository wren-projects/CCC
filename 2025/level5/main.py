from collections import defaultdict
import multiprocessing
from queue import PriorityQueue
import sys
from time import time as time_lib


def apply_acc(v, dv):
    if v == 0:
        return dv * 5
    if abs(v + dv) == 0:
        return v
    if abs(v + dv) == 6:
        return 0

    return v + dv


def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1

    return 0


K = 10


def solve(I, X, Y, aX, aY, MAX_T):
    start = time_lib()
    type State = tuple[int, int, int, int, int, int]
    grid: dict[State, list] = defaultdict(lambda: [float("inf"), [0], [0]])

    x = y = v_x = v_y = tick_x = tick_y = 0

    queue: PriorityQueue[tuple[int, int, State]] = PriorityQueue()
    queue.put((0, 0, (x, y, v_x, v_y, tick_x, tick_y)))

    while queue.qsize() > 0:
        _, time, state = queue.get()

        if time > MAX_T:
            continue

        x, y, v_x, v_y, tick_x, tick_y = state

        grid_time, moves_x, moves_y = grid[state]
        if grid_time < time:
            continue

        if abs(x - aX) <= 2 and abs(y - aY) <= 2:
            continue

        if x == X and y == Y and v_x == 0 and v_y == 0:
            elapsed = time_lib() - start
            print(f"Done {I} in {elapsed}", file=sys.stderr)
            return grid[state][1:]

        if (x**2 + y**2) ** 0.5 + ((x - X) ** 2 + (y - Y) ** 2) ** 0.5 >= (
            X**2 + Y**2
        ) ** 0.5 + K:
            continue

        for dv_x in range(-1, 2):
            new_x = x
            new_tick_x = tick_x - 1
            if new_tick_x >= 0:
                dv_x = 0

            new_moves_x = moves_x.copy()

            for dv_y in range(-1, 2):
                new_y = y
                new_tick_y = tick_y - 1
                if new_tick_y >= 0:
                    dv_y = 0

                new_moves_y = moves_y.copy()

                new_v_x = apply_acc(v_x, dv_x)
                new_v_y = apply_acc(v_y, dv_y)

                if new_tick_x == -1:
                    new_tick_x = max(abs(new_v_x), 1) - 1
                    new_x = x + sign(v_x)
                    new_moves_x.append(new_v_x)

                if new_tick_y == -1:
                    new_tick_y = max(abs(new_v_y), 1) - 1
                    new_y = y + sign(v_y)
                    new_moves_y.append(new_v_y)

                new_state = (new_x, new_y, new_v_x, new_v_y, new_tick_x, new_tick_y)
                new_time = time + 1

                if grid[new_state][0] > new_time:
                    new_heuristic = new_time + max(
                        abs(new_x - X) * abs(v_x), abs(new_y - Y) * abs(v_y)
                    )
                    queue.put((new_heuristic, new_time, new_state))

                    grid[new_state] = [new_time, new_moves_x, new_moves_y]

    raise Exception("No solution")


def main():
    Xs = []
    Ys = []
    aXs = []
    aYs = []
    Ts = []

    N = int(input())
    for i in range(N):
        XY, T = input().split()
        X, Y = map(int, XY.split(","))

        aX, aY = map(int, input().split(","))

        Xs.append(X)
        Ys.append(Y)
        aXs.append(aX)
        aYs.append(aY)
        Ts.append(int(T))

    with multiprocessing.Pool() as pool:
        for moves_x, moves_y in pool.starmap(
            solve, zip(range(N), Xs, Ys, aXs, aYs, Ts)
        ):
            print(*moves_x)
            print(*moves_y)


if __name__ == "__main__":
    main()
