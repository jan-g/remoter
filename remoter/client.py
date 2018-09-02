import asyncio
import inspect
import json
import sys

import aiohttp

import remoter.server


class Client:
    def __init__(self, cls, plr):
        self.cls = cls
        self.plr = plr
        self.url = None
        self.futures = {}

    def run(self, host='localhost', port=8080, game=None, pid=None):
        self.url = 'http://{}:{}/{}.{}'.format(host, port, self.cls.__module__, self.cls.__name__)

        asyncio.run(self.dispatch(game, pid))
        sys.exit(self.exit_code)

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

            g = GameProxy(self, game, pid, cls=self.cls)
            plr = self.plr(g)
            self.game = game
            self.pid = pid

            self.in_flight = set()
            self.completed = set()

            self.exit_code = None
            # Poll and dispatch events
            while self.exit_code is None:
                events = await self.get(game, 'player', pid, 'e')
                futures = await self.get(game, 'player', pid, 'f')
                launched = False

                if events != {}:
                    for k, ev in sorted((int(k), e) for k, e in events.items()):
                        if k not in self.in_flight:
                            # Do we run this inline or as a coroutine?
                            try:
                                _await = inspect.signature(getattr(plr, ev[0])).parameters['_await'].default
                            except (AttributeError, TypeError, KeyError):
                                # By default, we 'synchronously' call the server
                                _await = True
                            if _await:
                                await self.handle_event(k, plr, ev[0], ev[1], ev[2])
                            else:
                                self.in_flight.add(k)
                                asyncio.create_task(self.handle_event(k, plr, ev[0], ev[1], ev[2]))
                            launched = True
                if futures != {}:
                    print("futures:", futures)
                    for k, r in futures.items():
                        k = int(k)
                        launched = True
                        self.futures[k].set_result(r)
                        await self.delete(game, 'player', pid, 'f', k)
                        del self.futures[k]

                self.in_flight.difference_update(self.completed)
                self.completed = set()

                if not launched:
                    await asyncio.sleep(1)

    async def handle_event(self, key, plr, call, args, kwargs):
        print("launching", key, call, args, kwargs)
        try:
            result = await getattr(plr, call)(*args, **kwargs)
            await self.post(self.game, 'player', self.pid, 'e', key, args=result)
        except SystemExit as ex:
            await self.post(self.game, 'player', self.pid, 'e', key, args=str(ex))
            self.exit_code = ex.code
        except Exception as ex:
            # print("exception occurred handling player event", call, ex)
            await self.post(self.game, 'player', self.pid, 'e', key, args=str(ex))
        self.completed.add(key)

    async def post(self, *path, args=None, headers=None):
        path = '/'.join(str(p) for p in path)
        if path != '':
            path = '/' + path
        try:
            async with self.session.post(self.url + path, json=args, headers=headers) as resp:
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

    async def delete(self, *path):
        path = '/'.join(str(p) for p in path)
        if path != '':
            path = '/' + path
        try:
            async with self.session.delete(self.url + path) as resp:
                return await resp.json()
        except json.decoder.JSONDecodeError:
            return None


class GameProxy:
    def __init__(self, client, game, pid, cls=None):
        self.__client = client
        self.__game = game
        self.__pid = pid
        self.__cls = cls

    def __getattr__(self, call):
        # Check the method to see if it has a default for _await
        try:
            _await = inspect.signature(getattr(self.__cls, call)).parameters['_await'].default
        except (AttributeError, TypeError, KeyError):
            # By default, we 'synchronously' call the server
            _await = True

        async def c(*args, _await=_await, **kwargs):
            if len(args) > 0:
                kwargs[''] = args
            if _await:
                return await self.__client.post(self.__game, call, args=kwargs)
            else:
                # print("triggering a future")
                fid = await self.__client.post(self.__game, call, args=kwargs, headers={remoter.server.Server.REMOTER_HEADER: str(self.__pid)})
                # print("fid=", fid, type(fid))
                f = asyncio.Future()
                self.__client.futures[fid] = f
                result = await f
                # print("future returns", result)
                return result
        return c
