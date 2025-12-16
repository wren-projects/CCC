from collections import defaultdict
import multiprocessing
from queue import PriorityQueue
import sys
from time import time


def apply_acc(v, dv):
    """Apply acceleration to velocity."""
    if v == 0:
        return dv * 5
    if abs(v + dv) == 0:
        return v
    if abs(v + dv) == 6:
        return 0

    return v + dv


def sign(x):
    """Get the sign of a number."""
    if x > 0:
        return 1
    if x < 0:
        return -1

    return 0


K = 10


def solve(i, target_x, target_y, asteroid_x, asteroid_y, max_tick):
    start = time()
    type State = tuple[int, int, int, int, int, int]
    grid: dict[State, list] = defaultdict(lambda: [float("inf"), [0], [0]])

    x = y = v_x = v_y = tick_x = tick_y = 0

    queue: PriorityQueue[tuple[int, int, State]] = PriorityQueue()
    queue.put((0, 0, (x, y, v_x, v_y, tick_x, tick_y)))

    while queue.qsize() > 0:
        _, tick, state = queue.get()

        x, y, v_x, v_y, tick_x, tick_y = state

        grid_time, moves_x, moves_y = grid[state]
        if grid_time < tick:
            continue

        if x == target_x and y == target_y and v_x == 0 and v_y == 0:
            elapsed = time() - start
            print(f"Done {i} in {elapsed}", file=sys.stderr)
            return grid[state][1:]

        if tick >= max_tick:
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

                # if within 2 tiles of the astroid, skip
                if abs(new_x - asteroid_x) <= 2 and abs(new_y - asteroid_y) <= 2:
                    continue

                new_state = (new_x, new_y, new_v_x, new_v_y, new_tick_x, new_tick_y)
                new_tick = tick + 1

                if grid[new_state][0] > new_tick:
                    new_heuristic = (
                        new_tick + abs(new_x - target_x) + abs(new_y - target_y)
                    )
                    queue.put((new_heuristic, new_tick, new_state))

                    grid[new_state] = [new_tick, new_moves_x, new_moves_y]

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
