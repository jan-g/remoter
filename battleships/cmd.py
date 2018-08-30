import remoter.cmd
import battleships.game


def server():
    remoter.cmd.server(battleships.game.Game)


def client():
    remoter.cmd.client(battleships.game.Game, battleships.game.Player)


if __name__ == '__main__':
    server()
