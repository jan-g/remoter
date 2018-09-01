import asyncio
from remoter import BasePlayer
from battleships.board import Board, parse_ship_location, parse_bomb_location


ships = [("Carrier", 5),
         ("Battleship", 4),
         ("Cruiser", 3),
         ("Submarine",2),
         ("Destroyer", 2)]


class Game:
    def __init__(self):
        self.players = []
        self.boards = {}

    async def new_player(self, plr):
        if len(self.players) < 2:
            self.players.append(plr)

            # Keep tabs on this player's id number
            pn = plr.pn = len(self.players)

            self.boards[pn] = Board()

            # This player isn't yet ready. We track this because multiple
            # players can join in parallel; when each becomes ready, we check
            # to determine if everyone is good to go.
            plr.ready = False

            # Tell the player who they are, and ask them for their ship placements.
            await plr.get_ships(pn)

            # Once they're ready, check if everyone else is too.
            plr.ready = True

            # Is everyone ready?
            if len(self.players) > 1 and all(p.ready for p in self.players):
                # Could just use "await self.game_loop()" here.
                asyncio.create_task(self.game_loop())
        else:
            await plr.print("Too many players already connected to this game.")
            await plr.exit(0)

    async def my_board(self, pn):
        """This is called by the Player to return the image of their board.

        Used during get_ships.
        """
        board = self.boards[pn]
        return board.lines()

    async def add_ship(self, pn, x, y, dx, dy, size):
        """This is called by the Player to place a ship.

        If the ship is successfully placed, return True.
        """
        board = self.boards[pn]
        try:
            board.add_ship(x, y, dx, dy, size)
            return True
        except ValueError:
            return False

    async def game_loop(self):
        """Drive a game between two players.
        """
        other, player = self.players
        while not self.boards[other.pn].defeated():
            player, other = other, player

            x, y = await player.guess(self.boards[player.pn].lines(), self.boards[other.pn].other_lines())

            result = self.boards[other.pn].potshot(x, y)
            if result == Board.MISS:
                await player.print("Splash!")
            elif result == Board.NEAR:
                await player.print("KERSPLOOSH!!")
            else:
                await player.print("BOOM!!!")


        await player.print("The winner is {}".format(player.pn))
        await other.print("The winner is {}".format(player.pn))
        await player.exit(0)
        await other.exit(0)


class Player(BasePlayer):
    async def get_ships(self, pn):
        self.pn = pn
        print("Player {} pick your ships!".format(pn))
        print("Use: R C D for input (R: row; C: column; D = A for across, D for down)")

        for ship, size in ships:
            while True:
                print()
                await self.display()
                location = input("enter position of {}: ".format(ship))
                # We want three characters: the y-coord, the x-coord and an A or a D.
                try:
                    x, y, dx, dy = parse_ship_location(location)
                except:
                    print("Use: R C D for input (R: row; C: column; D = A for across, D for down)")
                    continue

                # Try to place the ship
                if not await self.game.add_ship(pn, x, y, dx, dy, size):
                    print("That ship can't go there!")
                    continue

                break

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

        while True:
            try:
                print()
                x, y = parse_bomb_location(input("Your guess? "))
                return x, y
            except KeyboardInterrupt:
                await self.exit(0)
            except Exception:
                pass


if __name__ == '__main__':
    import asyncio
    g = Game()
    p1 = Player(g)
    p2 = Player(g)
    asyncio.get_event_loop().run_until_complete(asyncio.gather(
        g.new_player(p1),
        g.new_player(p2)))