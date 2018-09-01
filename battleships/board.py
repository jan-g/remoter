from string import ascii_lowercase, digits


def parse_ship_location(loc):
    loc = loc.lower().strip().replace(" ", "")
    row = ascii_lowercase.index(loc[0])
    col = digits.index(loc[1])
    if loc[-1] == 'a':
        dx, dy = 1, 0
    elif loc[-1] == 'd':
        dx, dy = 0, 1
    return col, row, dx, dy


def parse_bomb_location(loc):
    loc = loc.lower().strip().replace(" ", "")
    row = ascii_lowercase.index(loc[0])
    col = digits.index(loc[1])
    return col, row


class Board:
    # potshots return one of these
    MISS = 0
    NEAR = 1
    HIT = 2

    # the board representation uses one of these
    SHIP = "S"
    GUESS = "."
    NEAR_GUESS = "!"
    SUNK = "X"

    def __init__(self, width=10, height=10):
        assert 0 < width <= 10
        assert 0 < height <= 10

        self.mx = width
        self.my = height

        # Coordinate pair -> ship, miss, near-miss.
        self.sea = {}

    def add_ship(self, x, y, dx, dy, size):
        """Add a ship fo a given length

        If it passes off the board, or abuts an already places ship, raise a ValueError
        """
        cells = {(x + i * dx, y + i * dy) for i in range(size)}
        if any(cx < 0 or cx >= self.mx or cy < 0 or cy >= self.my
               for (cx, cy) in cells):
            raise ValueError("That ship does not lie on the board")

        neighbours = {(cx + dx, cy + dy)
                      for dx in (-1, 0, 1)
                      for dy in (-1, 0, 1)
                      for (cx, cy) in cells}

        if any((nx, ny) in self.sea
               for (nx, ny) in neighbours):
            raise ValueError("That ship abuts another")

        for (cx, cy) in cells:
            self.add_counter(cx, cy)

    def add_counter(self, x, y):
        self.sea[x, y] = Board.SHIP

    def potshot(self, x, y):
        """Return MISS, NEAR or HIT"""
        if x < 0 or self.mx <= x or y < 0 or self.my <= y:
            raise ValueError("Off-grid shot")

        if self.sea.get((x, y)) == Board.SHIP:
            self.sea[x, y] = Board.SUNK
            return Board.HIT
        elif any(self.sea.get((x + dx, y + dy)) == Board.SHIP
                 for dx in (-1, 0, 1)
                 for dy in (-1, 0, 1)):
            self.sea[x, y] = Board.NEAR_GUESS
            return Board.NEAR
        else:
            self.sea[x, y] = Board.GUESS
            return Board.MISS

    def defeated(self):
        return not any(cell == Board.SHIP
                       for _, cell in self.sea.items())

    def display(self):
        print('\n'.join(self.lines()))

    def lines(self):
        d = ["  " + digits[:self.mx]]
        for y in range(self.my):
            line = ""
            for x in range(self.mx):
                line += self.sea.get((x, y), '~')
            d.append(ascii_lowercase[y] + ' ' + line)
        return d

    def other_lines(self):
        d = ["  " + digits[:self.mx]]
        for y in range(self.my):
            line = ""
            for x in range(self.mx):
                line += self.sea.get((x, y), '~').replace(Board.SHIP, '~')
            d.append(ascii_lowercase[y] + ' ' + line)
        return d
