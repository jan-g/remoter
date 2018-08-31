from collections import namedtuple
from json.decoder import JSONDecodeError
import random
from aiohttp import web
import asyncio


class Handler:
    def __init__(self, cls):
        self.cls = cls
        self.instances = {}

    def new(self):
        eh = EventHandler()
        i = self.cls()
        self.instances[id(i)] = (i, eh)
        return id(i)

    async def invoke(self, instance, method, args):
        m = getattr(self.instances[instance][0], method)
        try:
            pos = args.pop('')
        except KeyError:
            pos = ()
        if callable(m):
            return await m(*pos, **args)

    def new_player(self, instance):
        i, eh = self.instances[instance]
        player, pid = eh.new_player()
        try:
            print("about to launch coroutine")
            asyncio.create_task(i.new_player(player))
            print("launched coroutine")
        except Exception:
            pass
        return pid

    def player_events(self, instance, pid):
        return self.instances[instance][1].player_events(pid)

    def ack_event(self, instance, pid, event, result):
        self.instances[instance][1].ack_event(pid, event, result)


class PlayerProxy:
    def __init__(self, pid, eh):
        self.__pid = pid
        self.__eh = eh

    def __getattr__(self, call):
        # p.foo(a, b, c)  -> send an asynchronous foo(a, b, c)

        async def c(*args, **kwargs):
            # When called, register an event to the player
            future = asyncio.Future()
            n = self.__eh.post_event(self.__pid, call, args, kwargs, future)
            print("{} returned event {}".format(call, n))
            return await future
        return c

    def __enqueue(self, call, kwargs):
        self.eh.post_event()


Event = namedtuple('Event', ['call', 'args', 'kwargs', 'cb'])


class EventHandler:
    def __init__(self):
        self.events = {}

    def new_player(self):
        for i in range(1000):
            pid = random.randrange(8999) + 1000
            if pid not in self.events:
                self.events[pid] = (0, {})
                return PlayerProxy(pid, self), pid
        raise KeyError()

    def player_events(self, pid):
        return {n: (e.call, e.args, e.kwargs)
                for n, e in self.events[pid][1].items()}

    def ack_event(self, pid, n, result):
        cb = self.events[pid][1][n].cb
        cb.set_result(result)
        del self.events[pid][1][n]

    def post_event(self, pid, call, args, kwargs, future):
        n, events = self.events[pid]
        n += 1
        events[n] = Event(call, args, kwargs, future)
        self.events[pid] = (n, events)
        return n


class Server:
    def __init__(self):
        self.handlers = {}
        app = self.app = web.Application()
        app.add_routes([web.post('/{cls}', self.new),
                        web.post('/{cls}/{instance}/player', self.new_player),
                        web.get('/{cls}/{instance}/player/{pid}', self.player_events),
                        web.post('/{cls}/{instance}/player/{pid}/{event}', self.ack_player_event),
                        web.post('/{cls}/{instance}/{method}', self.invoke),
                        ])

    def run(self, host=None, port=None, debug=False):
        web.run_app(self.app, host=host, port=port)

    def register(self, cls):
        self.handlers[cls.__module__ + '.' + cls.__name__] = Handler(cls)

    # POST /<cls>
    async def new(self, request):
        cls = request.match_info['cls']
        return web.json_response(self.handlers[cls].new())

    # POST /<cls>/<instance>/<method> {"": [p1, p2, p3, ...], "arg1": "value1", ...}
    async def invoke(self, request):
        cls = request.match_info['cls']
        instance = int(request.match_info['instance'])
        method = request.match_info['method']

        try:
            args = await request.json()
        except JSONDecodeError:
            args = {}
        return web.json_response(await self.handlers[cls].invoke(instance, method, args))

    # POST /<cls>/<instance>/player
    async def new_player(self, request):
        cls = request.match_info['cls']
        instance = int(request.match_info['instance'])

        return web.json_response(self.handlers[cls].new_player(instance))

    # GET /<cls>/<instance>/player/<pid>
    async def player_events(self, request):
        cls = request.match_info['cls']
        instance = int(request.match_info['instance'])
        pid = int(request.match_info['pid'])

        return web.json_response(self.handlers[cls].player_events(instance, pid))

    # POST /<cls>/<instance>/player/<pid>/<event> result
    async def ack_player_event(self, request):
        cls = request.match_info['cls']
        instance = int(request.match_info['instance'])
        pid = int(request.match_info['pid'])
        event = int(request.match_info['event'])

        try:
            arg = await request.json()
        except JSONDecodeError:
            arg = None
        self.handlers[cls].ack_event(instance, pid, event, arg)
        return web.json_response()
