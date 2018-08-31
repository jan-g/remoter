import asyncio
import json
import aiohttp


class Client:
    def __init__(self, cls, plr):
        self.cls = cls
        self.plr = plr
        self.url = None

    def run(self, host='localhost', port=8080, game=None, pid=None):
        self.url = 'http://{}:{}/{}.{}'.format(host, port, self.cls.__module__, self.cls.__name__)

        asyncio.run(self.dispatch(game, pid))

    async def dispatch(self, game, pid):
        self.session = aiohttp.ClientSession()
        async with self.session:

            # Make a new game, if required
            if game is None:
                game = await self.post()
                pid = None
                print("--game", game)

            # Make a new PID, if required
            if pid is None:
                pid = await self.post(game, 'player')
                print("--as", pid)

            g = GameProxy(self, game, pid)
            plr = self.plr(g)

            # Poll and dispatch events
            while True:
                events = await self.get(game, 'player', pid)
                if events != {}:
                    for k, ev in sorted((int(k), e) for k, e in events.items()):
                        try:
                            result = await getattr(plr, ev[0])(*ev[1], **ev[2])
                            await self.post(game, 'player', pid, k, args=result)
                        except SystemExit as ex:
                            await self.post(game, 'player', pid, k, args=str(ex))
                            raise
                        except Exception as ex:
                            print("exception occurred handling player event", ev[0], ex)
                            await self.post(game, 'player', pid, k, args=str(ex))
                else:
                    await asyncio.sleep(1)

    async def post(self, *path, args=None):
        path = '/'.join(str(p) for p in path)
        if path != '':
            path = '/' + path
        try:
            async with self.session.post(self.url + path, json=args) as resp:
                return await resp.json()
        except json.decoder.JSONDecodeError:
            return None

    async def get(self, *path):
        path = '/'.join(str(p) for p in path)
        if path != '':
            path = '/' + path
        try:
            async with self.session.get(self.url + path) as resp:
                return await resp.json()
        except json.decoder.JSONDecodeError:
            return None


class GameProxy:
    def __init__(self, client, game, pid):
        self.__client = client
        self.__game = game
        self.__pid = pid

    def __getattr__(self, call):
        async def c(*args, **kwargs):
            if len(args) > 0:
                kwargs[''] = args
            return await self.__client.post(self.__game, call, args=kwargs)
        return c
