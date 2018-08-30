import json
import requests
import time


class Client:
    def __init__(self, cls, plr):
        self.cls = cls
        self.plr = plr
        self.url = None

    def run(self, host='localhost', port=8080, debug=False, game=None, pid=None):
        self.url = 'http://{}:{}/{}.{}'.format(host, port, self.cls.__module__, self.cls.__name__)

        # Make a new game, if required
        if game is None:
            game = self.post()
            pid = None
            print("--game", game)

        # Make a new PID, if required
        if pid is None:
            pid = self.post(game, 'player')
            print("--as", pid)

        g = GameProxy(self, game, pid)
        plr = self.plr(g)

        # Poll and dispatch events
        while True:
            events = self.get(game, 'player', pid)
            if events != {}:
                for k, ev in sorted((int(k), e) for k, e in events.items()):
                    try:
                        result = getattr(plr, ev[0])(*ev[1], **ev[2])
                        self.post(game, 'player', pid, k, args=result)
                    except Exception as ex:
                        print("exception occurred handling player event", ev[0], ex)
                        self.post(game, 'player', pid, k, args=str(ex))
            time.sleep(1)

    def post(self, *path, args=None):
        path = '/'.join(str(p) for p in path)
        if path != '':
            path = '/' + path
        try:
            return requests.post(self.url + path, json=args).json()
        except json.decoder.JSONDecodeError:
            return None

    def get(self, *path):
        path = '/'.join(str(p) for p in path)
        if path != '':
            path = '/' + path
        try:
            return requests.get(self.url + path).json()
        except json.decoder.JSONDecodeError:
            return None


class GameProxy:
    def __init__(self, client, game, pid):
        self.__client = client
        self.__game = game
        self.__pid = pid

    def __getattr__(self, call):
        def c(*args, **kwargs):
            if len(args) > 0:
                kwargs[''] = args
            return self.__client.post(self.__game, call, args=kwargs)
        return c
