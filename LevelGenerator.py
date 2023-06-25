from random import randint


class Generator:
    def __init__(self, grid_size_x, grid_size_y):
        self.grid_size_x = grid_size_x
        self.grid_size_y = grid_size_y
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

            self.set_field(self.x, self.y, 0)

            i += 1

        self.set_field(self.x + dir_x, self.y + dir_y, 3)

        assert self.in_bounds(self.x, self.y)

    def generate(self):
        self.set_field(self.x, self.y, 0)

        for i in range(1000):
            d = round(randint(0, 3))

            m = round(randint(1, max(self.grid_size_x, self.grid_size_y)))
            if d == 0:
                self.generate_line(1, 0, m)
            elif d == 1:
                self.generate_line(-1, 0, m)
            elif d == 2:
                self.generate_line(0, 1, m)
            elif d == 3:
                self.generate_line(0, -1, m)

        self.tiles = [1 if x == 3 else x for x in self.tiles]

        return self.tiles
