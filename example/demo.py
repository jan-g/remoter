from remoter import BasePlayer


class Demo:
    def __init__(self):
        print("new Demo instantiated")

    async def test(self, a=0, b=0):
        print("test called with {} and {}".format(a, b))
        return a + b

    async def new_player(self, p):
        print("new player {} registered".format(p))
        name = await p.input("what's your name? ")
        await p.welcome(msg="hello, {}".format(name))
        print("new player returned from welcome")

        result = await p.succ(5)
        print("result received:", result)

        await p.welcome("goodbye")
        print("also got here")
        await p.exit(0)
        print("client killed")


class Player(BasePlayer):
    async def welcome(self, msg=None):
        print("welcome: {}".format(msg))
        print("we try adding 6 and 7 and get:", await self.game.test(a=6, b=7))
        print("got here")

    async def succ(self, n):
        s = input("give the successor of {}: ".format(n))
        return s


if __name__ == '__main__':
    import asyncio
    g = Demo()
    p = Player(g)
    asyncio.run(g.new_player(p))
