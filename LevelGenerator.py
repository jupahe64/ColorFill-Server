from random import randint
from typing import Optional


class Generator:
    def __init__(self, grid_size_x, grid_size_y, max_effective_moves=10):
        self.grid_size_x = grid_size_x
        self.grid_size_y = grid_size_y
        self.max_effective_moves = max_effective_moves
        self.tiles = [1] * grid_size_x * grid_size_y

        self.x = 0
        self.y = 3

    def set_field(self, _x, _y, value):
        if not self.in_bounds(_x, _y):
            return
        self.tiles[_x + _y * self.grid_size_x] = value

    def field(self, _x, _y):
        if not self.in_bounds(_x, _y):
            return 1

        return self.tiles[_x + _y * self.grid_size_x]

    def in_bounds(self, x, y):
        if x < 0:
            return False

        if y < 3:
            return False

        if x >= self.grid_size_x:
            return False

        if y >= self.grid_size_y:
            return False

        return True

    def generate_line(self, dir_x, dir_y, max_length):
        was_effective = False
        i = 0

        while i < max_length or \
                self.field(self.x + dir_x, self.y + dir_y) == 0 or \
                self.field(self.x + dir_x, self.y + dir_y) == 2:
            _x = self.x + dir_x
            _y = self.y + dir_y

            if self.field(_x, _y) == 3 \
                    or not self.in_bounds(_x, _y):
                break

            self.x = _x
            self.y = _y

            if self.field(self.x, self.y) == 1:
                was_effective = True

            self.set_field(self.x, self.y, 0)

            i += 1

        self.set_field(self.x + dir_x, self.y + dir_y, 3)

        assert self.in_bounds(self.x, self.y)

        return was_effective

    def generate(self):
        RIGHT = 0
        DOWN = 1
        LEFT = 2
        UP = 3

        self.set_field(self.x, self.y, 0)

        effective_moves = 0

        for i in range(1000):
            d = round(randint(0, 3))

            if (
                    (d == LEFT and self.x == 0) or
                    (d == RIGHT and self.x == self.grid_size_x - 1) or
                    (d == UP and self.y == 0) or
                    (d == DOWN and self.y == self.grid_size_y - 1)
            ):
                d = (d+2) % 4

            m = round(randint(1, max(self.grid_size_x, self.grid_size_y)))
            if d == RIGHT:
                effective_moves += self.generate_line(1, 0, m)
            elif d == DOWN:
                effective_moves += self.generate_line(0, 1, m)
            elif d == LEFT:
                effective_moves += self.generate_line(-1, 0, m)
            elif d == UP:
                effective_moves += self.generate_line(0, -1, m)

            if effective_moves == self.max_effective_moves:
                break

        self.tiles = [1 if x == 3 else x for x in self.tiles]

        return self.tiles, effective_moves
