import heapq
from quads import QuadTree, BoundingBox
import sys
from collections import defaultdict
from multiprocessing import Pool
import time
from itertools import product


def apply_acc(v, dv):
    if v == 0:
        return dv * 5
    if v + dv == 0:
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


def changes(pos, v, tick, elapsed) -> list[tuple[int, int, int]]:
    """Returns list of possible (pos, v, tick) changes after elapsed ticks."""
    if tick >= elapsed:
        return [(pos, v, tick - elapsed)]

    new_x = pos + sign(v)
    return [
        (new_x, acc := apply_acc(v, dv), saturating_sub(abs(acc), 1))
        for dv in range(-1, 2)
    ]


def saturating_sub(x, y):
    return max(0, x - y)


type State = tuple[int, int, int, int, int, int]


class QueueItem:
    def __init__(
        self, heuristic: int, time: int, state: State, prev_state: State | None = None
    ):
        self.heuristic = heuristic
        self.time = time
        self.state = state
        self.prev_state = prev_state

    def __lt__(self, other):
        if self.heuristic != other.heuristic:
            return self.heuristic < other.heuristic

        return self.time < other.time

    def __eq__(self, other):
        return (
            self.heuristic == other.heuristic
            and self.time == other.time
            and self.state == other.state
        )


def check_collision(x, y, asteroids):
    """Check if position (x,y) collides with any asteroid in 3x3 area"""
    for ax, ay in asteroids:
        if abs(ax - x) <= 1 and abs(ay - y) <= 1:
            return True
    return False


def solve(i, x_target, y_target, asteroids, max_t):
    start_time = time.time()

    # assume all asteroids are within 1000x1000 grid
    asteroid_quad = QuadTree((0, 0), 1000, 1000)

    for ax, ay in asteroids:
        asteroid_quad.insert((ax, ay))

    state: State = (0, 0, 0, 0, 0, 0)  # x, y, v_x, v_y, tick_x, tick_y

    # Priority queue for A* search
    queue = [QueueItem(0, 2, state, None)]
    heapq.heapify(queue)

    grid = defaultdict(lambda: float("inf"))
    predecessors = {}

    while queue:
        item = heapq.heappop(queue)
        time_val, state, prev_state = item.time, item.state, item.prev_state

        if time_val > grid[state]:
            continue

        x, y, v_x, v_y, tick_x, tick_y = state

        if asteroid_quad.within_bb(BoundingBox(x - 1, y - 1, x + 1, y + 1)):
            continue

        grid[state] = time_val
        if prev_state is not None:
            predecessors[state] = prev_state

        # Check if we reached the target
        if x == x_target and y == y_target and v_x == 0 and v_y == 0:
            moves_x = [0]
            moves_y = [0]

            _, _, v_x, v_y, tick_x, tick_y = current_state = state
            while current_state in predecessors:
                _, _, prev_v_x, prev_v_y, prev_tick_x, prev_tick_y = (
                    prev_state
                ) = predecessors[current_state]

                if v_x != prev_v_x or tick_x >= prev_tick_x:
                    moves_x.append(prev_v_x)

                if v_y != prev_v_y or tick_y >= prev_tick_y:
                    moves_y.append(prev_v_y)

                current_state = prev_state

            moves_x.reverse()
            moves_y.reverse()

            elapsed = time.time() - start_time
            print(
                f"Done {i} in {elapsed:.3f}s with {time_val}/{max_t} steps",
                file=sys.stderr,
            )

            return moves_x, moves_y

        # next meaningful tick
        elapsed = min(tick_x, tick_y) + 1
        new_time = time_val + elapsed

        if new_time > max_t:
            continue

        # possible x changes
        x_changes = changes(x, v_x, tick_x, elapsed)

        # possible y changes
        y_changes = changes(y, v_y, tick_y, elapsed)

        for (new_x, new_v_x, new_tick_x), (new_y, new_v_y, new_tick_y) in product(
            x_changes, y_changes
        ):
            new_state = (new_x, new_y, new_v_x, new_v_y, new_tick_x, new_tick_y)

            if new_time >= grid[new_state]:
                continue

            grid[new_state] = new_time

            new_heuristic = new_time + abs(new_x - x_target) + abs(new_y - y_target)

            heapq.heappush(queue, QueueItem(new_heuristic, new_time, new_state, state))

    raise Exception(f"No solution found for task {i}")


def main():
    n = int(input())

    tasks = []

    for i in range(n):
        line = input()
        xy, t = line.split()

        coords = list(map(int, xy.split(",")))
        x, y = coords[0], coords[1]

        _num_asteroids = int(input())

        asteroid_line = input()

        asteroids: list[tuple[int, int]] = []
        for asteroid_str in asteroid_line.strip().split():
            asteroid_coords = list(map(int, asteroid_str.split(",")))
            asteroids.append((asteroid_coords[0], asteroid_coords[1]))

        tasks.append((i, x, y, asteroids, int(t)))

    # Process in parallel
    with Pool() as pool:
        results = pool.starmap(solve, tasks)

    # Output results in order
    for i, result in enumerate(results):
        if result is not None:
            moves_x, moves_y = result
            print(" ".join(map(str, moves_x)))
            print(" ".join(map(str, moves_y)))
            print()
        else:
            print(f"Error solving case {i}: No solution", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
