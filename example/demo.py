class Demo:
    def __init__(self, event_handler=None):
        print("new Demo instantiated")
        self.event_handler = event_handler

    def test(self, a=0, b=0):
        print("test called with {} and {}".format(a, b))
        return a + b

    def new_player(self, pid):
        print("new player {} registered".format(pid))
        self.event_handler.post_event(pid, "welcome")
