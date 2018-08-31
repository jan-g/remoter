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
        self.boards = []

    async def new_player(self, plr):
        if len(self.boards) < 2:
            board = Board()
            board.plr = plr
            pn = board.pn = len(self.boards)
            self.boards.append(board)
            await plr.welcome("welcome!", pn)
            board.ready = False
            await plr.get_ships()

            # Once we're ready, make sure everyone else is too.
            self.boards[pn].ready = True
            # Is everyone ready?
            print("is everyone ready?")
            if len(self.boards) > 1 and all(b.ready for b in self.boards):
                # Could just use "await self.game_loop()" here.
                asyncio.create_task(self.game_loop())

    async def display(self, pn):
        board = self.boards[pn]
        return board.display_str()

    async def add_ship(self, pn, x, y, dx, dy, size):
        board = self.boards[pn]
        try:
            board.add_ship(x, y, dx, dy, size)
            return True
        except ValueError:
            return False

    async def game_loop(self):
        player, other = self.boards
        while not other.defeated():
            player, other = other, player
            plr = player.plr

            await plr.print("{}. your turn".format(player.pn))
            await plr.print()
            await plr.print("Your board:")
            await plr.display()

            await plr.print()
            await plr.print("Their board:")
            await plr.print('\n'.join(other.other_str()))

            x, y = await plr.guess()  # Asynchronously call this then carry on with the returned result

            result = other.potshot(x, y)
            if result == Board.MISS:
                await plr.print("Splash!")
            elif result == Board.NEAR:
                await plr.print("KERSPLOOSH!!")
            else:
                await plr.print("BOOM!!!")


        await player.plr.print("The winner is {}".format(player.name))
        await other.plr.print("The winner is {}".format(player.name))
        await player.plr.exit(0)
        await other.plr.exit(0)


class Player(BasePlayer):
    async def welcome(self, msg, pn):
        print(msg)
        print("You are player", pn)
        self.pn = pn

    async def get_ships(self):
        print("Player {} pick your ships!".format(self.pn))
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
                if not await self.game.add_ship(self.pn, x, y, dx, dy, size):
                    print("That ship can't go there!")
                    continue

                break

        await self.display()

    async def display(self):
        print('\n'.join(await self.game.display(self.pn)))

    async def guess(self):
        while True:
            try:
                x, y = parse_bomb_location(input("your guess?"))
                return x, y
            except KeyboardInterrupt:
                await self.exit(0)
            except:
                pass


if __name__ == '__main__':
    import asyncio
    g = Game()
    p1 = Player(g)
    p2 = Player(g)
    asyncio.get_event_loop().run_until_complete(asyncio.gather(
        g.new_player(p1),
        g.new_player(p2)))