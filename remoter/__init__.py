import sys


class BasePlayer:
    def __init__(self, game=None):
        self.game = game

    async def print(self, *args, **kwargs):
        print(*args, **kwargs)

    async def input(self, *args, **kwargs):
        return input(*args, **kwargs)

    async def exit(self, status):
        sys.exit(status)
