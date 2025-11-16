from copy import deepcopy
from dataclasses import dataclass

# _input = input
# input = lambda: _input().strip()
stdin = open("level4_example.in")
input = lambda: stdin.readline().strip()

N = int(input())


def find_tree(W, H, field):
    for y in range(H):
        for x in range(W):
            if field[y][x] == "X":
                return x, y

    raise ValueError


@dataclass
class State:
    x: int
    y: int
    movements: str
    field: list[list[str]]
    W: int
    H: int

    def move(self, dx, dy):
        x = self.x + dx
        y = self.y + dy

        if x < 0 or x >= self.W or y < 0 or y >= self.H:
            raise ValueError

        if self.field[y][x] == "X":
            self.movements += "X"

        if self.field[y][x] == "#":
            raise ValueError

        self.x = x
        self.y = y
        self.field[y][x] = "#"

        move = ""

        if dx == 1:
            move = "D"
        elif dx == -1:
            move = "A"
        elif dy == 1:
            move = "S"
        elif dy == -1:
            move = "W"

        self.movements += move

    def can_move(self, dx, dy):
        x = self.x + dx
        y = self.y + dy
        return not (
            x < 0 or x >= self.W or y < 0 or y >= self.H or self.field[y][x] == "#"
        )

    # move up to N
    def move_n(self, dx, dy, n):
        for _ in range(n):
            if not self.can_move(dx, dy):
                break

            self.move(dx, dy)

    def move_max(self, dx, dy):
        while self.can_move(dx, dy):
            self.move(dx, dy)

    def move_to(self, dx, dy, tx, ty):
        if self.x == tx or self.y == ty:
            return
        while self.can_move(dx, dy) and self.x + dx != tx and self.y + dy != ty:
            self.move(dx, dy)

    # move max but leave space at the edge
    def move_with_space(self, dx, dy, space):
        while (
            self.can_move(dx, dy)
            and 0 <= self.x + dx * (space + 1) < self.W
            and 0 <= self.y + dy * (space + 1) < self.H
        ):
            self.move(dx, dy)

    def neighbors(self):
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if self.can_move(dx, dy):
                yield dx, dy

    def __repr__(self) -> str:
        f = "\n".join(["".join(row) for row in self.field])
        return f"({self.x}, {self.y})\n{f}"


def solve():
    W, H = map(int, input().split())

    field = [list(input()) for _ in range(H)]

    tree_x, tree_y = find_tree(W, H, field)

    state = State(x=0, y=0, movements="", field=deepcopy(field), W=W, H=H)

    if W % 2 == 0:
        state.move_max(1, 0)

        y_direction = 1

        while True:
            state.move_max(0, y_direction)
            if state.x == 0 and state.y == 0:
                break
            state.move(-1, 0)

            y_direction *= -1
    else:
        state.move_max(0, 1)

        x_direction = 1

        while True:
            state.move_max(x_direction, 0)
            if state.x == 0 and state.y == 0:
                break
            state.move(0, -1)
            x_direction *= -1

    print("Done")

    x_position = state.movements.find("X")
    correct_movements = state.movements[x_position + 3 :] + state.movements[:x_position]
    print(correct_movements)


for _ in range(N):
    solve()
