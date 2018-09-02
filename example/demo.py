from remoter import BasePlayer


class Demo:
    def __init__(self):
        print("new Demo instantiated")

    # This is called from the client, but returns immediately. We set _await=True (the default)
    async def test(self, a=0, b=0, _await=True):
        print("test called with {} and {}".format(a, b))
        return a + b

    async def new_player(self, p):
        self.player = p

        print("new player {} registered".format(p))
        name = await p.input("what's your name? ")
        await p.welcome(msg="hello, {}".format(name))
        print("new player returned from welcome")

        result = await p.succ(5)
        print("result received:", result)

        # A callback that triggers another callback
        print("long callback gives:", await p.long_callback(1))

        await p.welcome("goodbye")
        print("also got here")
        await p.exit(0)
        print("client killed")

    # This is called from the client, but makes further callouts. Therefore, we need to set _await=False
    # to mark it as a "long-running" request.
    async def ping(self, x, _await=False):
        # Called from the player, but also triggers outgoing events
        return await self.player.pong(x + 1) + 1


class Player(BasePlayer):
    async def welcome(self, msg=None):
        print("welcome: {}".format(msg))
        print("we try adding 6 and 7 and get:", await self.game.test(a=6, b=7))
        print("got here")

    async def succ(self, n):
        s = input("give the successor of {}: ".format(n))
        return s

    # This is called by the server, and makes long-lived calls back to it. Thus, mark it as _await=False
    async def long_callback(self, x, _await=False):
        print("player in long_callback, x={}, calling server".format(x))
        # self.game.ping(..., _await=False) means that this routine must also be marked with _await=False
        return await self.game.ping(x + 1)

    async def pong(self, x):
        print("player in pong, x={}, returning value to server".format(x))
        return x + 1


if __name__ == '__main__':
    import asyncio
    g = Demo()
    p = Player(g)
    asyncio.run(g.new_player(p))
