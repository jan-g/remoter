from collections import namedtuple
import random
import flask


class Handler:
    def __init__(self, cls):
        self.cls = cls
        self.instances = {}

    def new(self):
        eh = EventHandler()
        i = self.cls()
        self.instances[id(i)] = (i, eh)
        return str(id(i))

    def invoke(self, instance, method, args):
        m = getattr(self.instances[instance][0], method)
        try:
            pos = args.pop('')
        except KeyError:
            pos = ()
        if callable(m):
            return m(*pos, **args)

    def new_player(self, instance):
        i, eh = self.instances[instance]
        player, pid = eh.new_player()
        try:
            i.new_player(player)
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
        # @p.foo(a, b, c)
        # def bar(result): -> also register a callback
        def c(*args, **kwargs):
            # When called, register an event to the player
            n = self.__eh.post_event(self.__pid, call, args, kwargs)
            print("{} returned event {}".format(call, n))

            def dec(fn):
                print("decorating function {} to accept cb for {} item {}".format(fn.__name__, call, n))
                self.__eh.add_callback(self.__pid, n, fn)
            return dec
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
        try:
            if callable(cb):
                cb(result)
        except Exception as ex:
            print("callback excepted:", ex)
        del self.events[pid][1][n]

    def post_event(self, pid, call, args, kwargs):
        n, events = self.events[pid]
        n += 1
        events[n] = Event(call, args, kwargs, None)
        self.events[pid] = (n, events)
        return n

    def add_callback(self, pid, n, cb):
        _, events = self.events[pid]
        e = events[n]
        events[n] = Event(e.call, e.args, e.kwargs, cb)


class Server:
    def __init__(self):
        self.handlers = {}
        app = self.app = flask.Flask('remoter')
        app.route('/<cls>', methods=['POST'])(self.new)
        app.route('/<cls>/<int:instance>/<method>', methods=['POST'])(self.invoke)
        app.route('/<cls>/<int:instance>/player', methods=['POST'])(self.new_player)
        app.route('/<cls>/<int:instance>/player/<int:pid>', methods=['GET'])(self.player_events)
        app.route('/<cls>/<int:instance>/player/<int:pid>/<int:event>', methods=['POST'])(self.ack_player_event)

    def run(self, host=None, port=None, debug=False):
        self.app.run(host=host, port=port, debug=debug)

    def register(self, cls):
        self.handlers[cls.__module__ + '.' + cls.__name__] = Handler(cls)

    # POST /<cls>
    def new(self, cls):
        return self.handlers[cls].new()

    # POST /<cls>/<instance>/<method> {"": [p1, p2, p3, ...], "arg1": "value1", ...}
    def invoke(self, cls, instance, method):
        args = flask.request.get_json(force=True)
        return flask.jsonify(self.handlers[cls].invoke(instance, method, args))

    # POST /<cls>/<instance>/player
    def new_player(self, cls, instance):
        return flask.jsonify(self.handlers[cls].new_player(instance))

    # GET /<cls>/<instance>/player/<pid>
    def player_events(self, cls, instance, pid):
        return flask.jsonify(self.handlers[cls].player_events(instance, pid))

    # POST /<cls>/<instance>/player/<pid>/<event> result
    def ack_player_event(self, cls, instance, pid, event):
        try:
            arg = flask.request.get_json(force=True)
        except Exception as ex:
            arg = None
        self.handlers[cls].ack_event(instance, pid, event, arg)
        return ""
