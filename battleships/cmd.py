import remoter.cmd
import battleships.game
import battleships.bot


def server():
    remoter.cmd.server(battleships.game.Game)


def client():
    remoter.cmd.client(battleships.game.Game, battleships.game.Player)


def bot():
    remoter.cmd.client(battleships.game.Game, battleships.bot.SmarterBot)


if __name__ == '__main__':
    server()
