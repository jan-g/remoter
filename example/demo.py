class Demo:
    def __init__(self):
        print("new Demo instantiated")

    def test(self, a=0, b=0):
        print("test called with {} and {}".format(a, b))
        return a + b

    def new_player(self, p):
        print("new player {} registered".format(p.__pid))
        p.welcome(msg="hello, world")

        # Trigger a call on the player; when it returns, pass the result on
        @p.succ(5)
        def _(result):
            print("result received:", result)

        p.welcome("bar")
        print("also got here")


class Player:
    def __init__(self, game=None):
        self.game = game

    def welcome(self, msg=None):
        print("welcome: {}".format(msg))
        print("we try adding 6 and 7 and get:", self.game.test(a=6, b=7))

    def succ(self, n):
        s = input("give the successor of {}".format(n))
        return s
