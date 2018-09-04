from collections import namedtuple
import random
from remoter import BasePlayer
from battleships.board import Board, ships
from battleships.game import Game


Placement = namedtuple('Placement', ['x', 'y', 'dx', 'dy', 'cells', 'size'])
Coord = namedtuple('Coord', ['x', 'y'])


def cells(x, y, dx, dy, size):
    return frozenset(Coord(x + i * dx, y + i * dy) for i in range(size))


def possible_placements(board, size):
    """Return a set of Placements"""
    return {Placement(x, y, 1, 0, cells(x, y, 1, 0, size), size)
            for x in range(board.mx - size + 1)
            for y in range(board.my)}.union(
           {Placement(x, y, 0, 1, cells(x, y, 0, 1, size), size)
            for x in range(board.mx)
            for y in range(board.my - size + 1)})


def parse_other(lines):
    """Parse a series of lines in the format:
      0123456789
    a ~~~~~~~~~~
    ...
    j ~~~~~~~~~~

    Return a map of [x, y] -> MISS, NEAR_MISS or SUNK"""
    parse = {}
    for y, line in enumerate(lines[1:]):
        for x, c in enumerate(line[2:]):
            if c == Board.GUESS:
                parse[x, y] = Board.GUESS
            elif c == Board.NEAR_GUESS:
                parse[x, y] = Board.NEAR_GUESS
            elif c == Board.SUNK:
                parse[x, y] = Board.SUNK
    return parse


class Bot(BasePlayer):
    async def get_ships(self, pn):
        self.pn = pn
        print("Player {} pick your ships!".format(pn))
        print("Use: R C D for input (R: row; C: column; D = A for across, D for down)")

        b = Board()
        for ship, size in ships:
            possibles = [p
                         for p in possible_placements(b, size)
                         if all({(c.x + dx, c.y + dy) not in b.sea
                                 for dx in (-1, 0, 1)
                                 for dy in (-1, 0, 1)
                                 for c in p.cells})]

            place = random.choice(possibles)
            b.add_ship(place.x, place.y, place.dx, place.dy, place.size)

            print('Adding {} at ({}, {}) - ({}, {})'.format(ship,
                                                            place.x, place.y,
                                                            place.x + place.dx * (place.size - 1), place.y + place.dy * (place.size - 1)))
            assert await self.game.add_ship(pn, place.x, place.y, place.dx, place.dy, place.size)
            print()
            await self.display()

        print()
        print("Your final board:")
        await self.display()

    async def display(self):
        # This must be a coroutine since it uses `await` - making a call back to the Game server
        print('\n'.join(await self.game.my_board(self.pn)))

    async def guess(self, my_lines, other_lines):
        print()
        print("Player {}, it's your go!".format(self.pn))
        print()
        print("Your board", "Their board", sep='\t')
        for me, them in zip(my_lines, other_lines):
            print(me, them, sep='\t')

        state = parse_other(other_lines)

        coords = [(x, y)
                  for y in range(10)
                  for x in range(10)
                  if (x, y) not in state]

        return random.choice(coords)


class SmarterBot(Bot):
    async def guess(self, my_lines, other_lines):
        print()
        print("Player {}, it's your go!".format(self.pn))
        print()
        print("Your board", "Their board", sep='\t')
        for me, them in zip(my_lines, other_lines):
            print(me, them, sep='\t')

        state = parse_other(other_lines)

        for x, y in list(state):
            if state[x, y] == Board.SUNK:
                state[x-1, y-1] = Board.NEAR_GUESS
                state[x+1, y-1] = Board.NEAR_GUESS
                state[x-1, y+1] = Board.NEAR_GUESS
                state[x+1, y+1] = Board.NEAR_GUESS
            elif state[x, y] == Board.GUESS:
                # A guess that's not near anything should rule out the surrounding squares
                state.update({(x + dx, y + dy): ''
                              for dx in (-1, 0, 1)
                              for dy in (-1, 0, 1)})

        coords = [(x, y)
                  for y in range(10)
                  for x in range(10)
                  if (x, y) not in state]

        return random.choice(coords)


if __name__ == '__main__':
    import asyncio
    g = Game()
    p1 = Bot(g)
    p2 = SmarterBot(g)
    asyncio.get_event_loop().run_until_complete(asyncio.gather(
        g.new_player(p1),
        g.new_player(p2)))